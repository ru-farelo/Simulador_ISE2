import uuid

from sqlalchemy.orm import Session

from app.data.writing_prompts import FIXED_PROMPTS
from app.models.db_models import PracticeSession
from app.models.schemas import ErrorItem
from app.models.writing import ModelSentence, WritingCorrectionResult, WritingPrompt, WritingSubmission
from app.services.anthropic_client import structured_completion
from app.services.grading_common import band_from_score
from app.services.rag_service import format_context_block, log_retrieval, retrieve

GENRE_REGISTER_NOTE = {
    "essay": "formal register, no contractions, clear paragraph structure (intro/development/conclusion)",
    "article": "semi-formal, engaging register suitable for a magazine, can address the reader directly",
    "letter": "formal register, no contractions, appropriate greeting and closing for a letter of complaint",
    "review": "semi-formal register, descriptive and evaluative language, can be more personal in tone",
}

GENERATE_SYSTEM_PROMPT = (
    "You are an item writer for the Trinity College London ISE II exam (CEFR B2), "
    "Extended Writing task (Task 4). You write ORIGINAL writing prompts of varying "
    "genre — essay, article, letter, or review — never the same genre twice in a "
    "row. Each prompt must be answerable in 150-180 words and have a clear register "
    "expectation for its genre."
)

GENERATE_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "genre": {"type": "string", "enum": ["essay", "article", "letter", "review"]},
        "title": {"type": "string"},
        "instructions": {"type": "string", "description": "2-3 sentence task instructions, B2 level"},
    },
    "required": ["genre", "title", "instructions"],
}

CORRECT_SYSTEM_PROMPT = (
    "You are an experienced Trinity College London ISE II examiner (CEFR B2) marking "
    "a candidate's Extended Writing (Task 4) submission. Judge organisation, register "
    "appropriateness for the given genre, range and accuracy of vocabulary, and "
    "grammatical control. Be encouraging but precise.\n\n"
    "This candidate has 8 known recurring error types: gerunds after prepositions, "
    "modal perfects, cleft sentences, Present Perfect vs Past Simple confusion, "
    "impersonal passive voice, adverb placement, 'ultimately' vs 'lately' confusion, "
    "and overuse of 'very' before a noun instead of a stronger adjective. Watch for "
    "these WITH EXTRA ATTENTION, but only report an error if it is a genuine mistake "
    "that is actually present in the text — never invent an example of one of these "
    "categories to fill a quota, never flag a sentence that is grammatically correct, "
    "and never include an 'error' whose own correction says no change is needed. If "
    "the candidate's writing is clean, it is entirely correct for the errors list to "
    "be short or empty — a clean text should be praised in `strengths`, not padded "
    "with invented errors. Every entry in the errors list must be a real mistake with "
    "a real fix.\n\n"
    "Also pick ONE sentence from the candidate's text — ideally one with room for "
    "improvement, but if the text is very strong throughout, simply pick a good "
    "sentence and elevate it further — and rewrite it at a stronger B2/C1 level, "
    "explaining what changed."
)

CORRECT_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "number", "minimum": 0, "maximum": 100},
        "summary": {"type": "string", "description": "2-3 sentence overall comment"},
        "strengths": {
            "type": "array",
            "items": {"type": "string"},
            "description": "2-4 short bullet points on what the candidate did well",
        },
        "errors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "excerpt": {"type": "string"},
                    "correction": {"type": "string"},
                    "explanation": {"type": "string"},
                },
                "required": ["category", "excerpt", "correction", "explanation"],
            },
        },
        "model_sentence": {
            "type": "object",
            "properties": {
                "original": {"type": "string"},
                "rewritten": {"type": "string"},
                "explanation": {"type": "string"},
            },
            "required": ["original", "rewritten", "explanation"],
        },
    },
    "required": ["score", "summary", "strengths", "errors", "model_sentence"],
}


def get_fixed_prompt(prompt_id: str | None = None) -> WritingPrompt:
    import random

    if prompt_id:
        match = next((p for p in FIXED_PROMPTS if p["id"] == prompt_id), None)
        if match is None:
            raise ValueError(f"Unknown prompt id: {prompt_id}")
    else:
        match = random.choice(FIXED_PROMPTS)
    return WritingPrompt(**match, source="fixed")


def generate_prompt() -> WritingPrompt:
    result = structured_completion(
        system=GENERATE_SYSTEM_PROMPT,
        user_content="Write one new Extended Writing prompt.",
        tool_name="submit_prompt",
        tool_description="Submit the generated writing prompt.",
        input_schema=GENERATE_TOOL_SCHEMA,
        max_tokens=500,
    )
    return WritingPrompt(
        id=f"generated-{uuid.uuid4().hex[:8]}",
        source="generated",
        genre=result["genre"],
        title=result["title"],
        instructions=result["instructions"],
    )


def _word_count(text: str) -> int:
    return len([w for w in text.split() if w.strip()])


def correct_submission(db: Session, submission: WritingSubmission) -> WritingCorrectionResult:
    word_count = _word_count(submission.text)
    register_note = GENRE_REGISTER_NOTE.get(submission.genre, "")

    rag_query = f"{submission.title} {submission.genre} writing"
    retrieved = retrieve(rag_query, top_k=3)
    if retrieved:
        log_retrieval(db, rag_query, retrieved, used_in="writing_grading")
    context_block = format_context_block(retrieved)

    user_content = (
        f"Genre: {submission.genre} (expected register: {register_note})\n"
        f"Task title: {submission.title}\n"
        f"Task instructions: {submission.instructions}\n"
        f"Target length: 150-180 words. Candidate's word count: {word_count}.\n\n"
        f"Candidate's submission:\n{submission.text}"
        + (f"\n\n{context_block}" if context_block else "")
    )

    result = structured_completion(
        system=CORRECT_SYSTEM_PROMPT,
        user_content=user_content,
        tool_name="submit_correction",
        tool_description="Submit the marking result for the candidate's Extended Writing submission.",
        input_schema=CORRECT_TOOL_SCHEMA,
        max_tokens=2500,
    )

    band = band_from_score(result["score"])

    session_row = PracticeSession(
        skill="writing",
        sub_type=f"{submission.genre}:{submission.prompt_id}",
        duration_seconds=submission.duration_seconds,
        score=result["score"],
        band=band,
        summary=result["summary"],
        errors=result["errors"],
        raw_response=result,
    )
    db.add(session_row)
    db.commit()
    db.refresh(session_row)

    return WritingCorrectionResult(
        session_id=session_row.id,
        word_count=word_count,
        band=band,
        summary=result["summary"],
        strengths=result["strengths"],
        errors=[ErrorItem(**e) for e in result["errors"]],
        model_sentence=ModelSentence(**result["model_sentence"]),
        created_at=session_row.created_at,
    )
