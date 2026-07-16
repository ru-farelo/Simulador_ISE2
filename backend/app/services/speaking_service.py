import random

from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from app.models.db_models import PracticeSession, SpeakingTranscriptTurn
from app.models.schemas import ErrorItem
from app.models.speaking import (
    ConversationTurn,
    SpeakingCorrectionRequest,
    SpeakingCorrectionResult,
    SpeakingTaskName,
    SpeakingTurnRequest,
    SpeakingTurnResponse,
)
from app.services.anthropic_client import structured_completion
from app.services.grading_common import band_from_score
from app.services.rag_service import format_context_block, log_retrieval, retrieve

CONVERSATION_TOPICS = [
    "environment",
    "society",
    "values",
    "work",
    "education",
    "technology",
    "health",
    "travel",
]

BASE_PERSONA = (
    "You are a warm but professional Trinity College London ISE II examiner "
    "conducting the Speaking & Listening module with a B2-level candidate. "
    "Always reply in natural, conversational spoken English — contractions "
    "are fine, short turns of 1-3 sentences, never write like an essay."
)

TASK_INSTRUCTIONS: dict[SpeakingTaskName, str] = {
    "topic": (
        BASE_PERSONA
        + "\n\nThis is the Topic discussion (~4 minutes). The candidate has just delivered "
        "a prepared talk on their chosen topic. Ask natural follow-up questions about what "
        "they specifically said — probe their opinions, ask for a concrete example, or "
        "gently challenge a point they made. Ask ONE question at a time. After 3 candidate "
        "answers to your questions, set task_complete=true and give a brief natural closing "
        "remark instead of another question."
    ),
    "collaborative": (
        BASE_PERSONA
        + "\n\nThis is the Collaborative task (~4 minutes). The ROLES ARE REVERSED here: YOU "
        "present a brief dilemma or opinion, and the CANDIDATE must ask you questions to "
        "extract more information from you — they are interviewing you. Do not reveal every "
        "detail at once: mention only one new piece of information per answer, and wait for "
        "their next question before revealing more. If they ask about something you have not "
        "decided yet, invent a plausible detail on the spot and stay consistent with it for "
        "the rest of the conversation. If the history is empty, START the task by presenting "
        "a short dilemma or opinion in 2-3 sentences, without going into detail, then wait. "
        "After about 4 candidate questions, set task_complete=true and wrap up naturally."
    ),
    "conversation": (
        BASE_PERSONA
        + "\n\nThis is the general Conversation task (2-4 minutes) on the topic of '{topic}'. "
        "Ask natural conversational questions on this topic, one at a time, reacting "
        "genuinely to what the candidate says. If the history is empty, START with an "
        "opening question on this topic. After about 4 candidate answers, set "
        "task_complete=true and close naturally."
    ),
}

TURN_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "examiner_text": {"type": "string"},
        "task_complete": {"type": "boolean"},
    },
    "required": ["examiner_text", "task_complete"],
}


def pick_conversation_topic() -> str:
    return random.choice(CONVERSATION_TOPICS)


def _format_history(history: list[ConversationTurn]) -> str:
    if not history:
        return "(the conversation has not started yet)"
    return "\n".join(f"{turn.role.upper()}: {turn.text}" for turn in history)


# Number of candidate follow-up turns after which the task should wrap up.
# For "topic", the candidate's opening monologue doesn't count as a follow-up.
FOLLOWUP_LIMITS: dict[SpeakingTaskName, int] = {"topic": 3, "collaborative": 4, "conversation": 4}


def _persist_transcript(db: Session, conversation_id: str, task_name: str, turns: list[ConversationTurn]) -> None:
    """Idempotent: replaces whatever was stored for this conversation_id
    with the given turns, keyed by position. Called after every turn with
    the full history-so-far, so a partial conversation is never lost even
    if the candidate abandons it before requesting a correction.
    """
    db.execute(delete(SpeakingTranscriptTurn).where(SpeakingTranscriptTurn.conversation_id == conversation_id))
    for index, turn in enumerate(turns):
        db.add(
            SpeakingTranscriptTurn(
                conversation_id=conversation_id,
                task_name=task_name,
                turn_index=index,
                speaker=turn.role,
                text=turn.text,
            )
        )
    db.commit()


def get_examiner_turn(db: Session, task_name: SpeakingTaskName, request: SpeakingTurnRequest) -> SpeakingTurnResponse:
    history, context = request.history, request.context
    system_prompt = TASK_INSTRUCTIONS[task_name].format(**context) if task_name == "conversation" else TASK_INSTRUCTIONS[task_name]

    candidate_turns = sum(1 for t in history if t.role == "candidate")
    followup_answers = candidate_turns - 1 if task_name == "topic" and candidate_turns > 0 else candidate_turns

    extra_context = ""
    if task_name == "topic" and context.get("notes"):
        extra_context = f"\nCandidate's prep notes for their talk: {context['notes']}"

    limit = FOLLOWUP_LIMITS[task_name]
    if followup_answers >= limit:
        stop_instruction = (
            f"The candidate has now answered {followup_answers} follow-up turns, which reaches "
            "the target for this task. You MUST set task_complete=true and reply with a brief, "
            "natural closing remark — do NOT ask a new question."
        )
    else:
        stop_instruction = (
            f"The candidate has answered {followup_answers} of an expected {limit} follow-up "
            "turns so far. Continue with task_complete=false and one more natural turn."
        )

    user_content = (
        f"{stop_instruction}{extra_context}\n\n"
        f"Conversation so far:\n{_format_history(history)}\n\n"
        "Produce your next reply as the examiner."
    )

    result = structured_completion(
        system=system_prompt,
        user_content=user_content,
        tool_name="submit_turn",
        tool_description="Submit the examiner's next conversational turn.",
        input_schema=TURN_TOOL_SCHEMA,
        max_tokens=400,
    )
    response = SpeakingTurnResponse(**result)

    full_history = [*history, ConversationTurn(role="examiner", text=response.examiner_text)]
    _persist_transcript(db, request.conversation_id, task_name, full_history)

    return response


PART_LABELS = {
    "topic": "Topic discussion",
    "collaborative": "Collaborative task",
    "conversation": "Conversation task",
    "listening": "Independent Listening",
}

CORRECT_SYSTEM_PROMPT = (
    "You are an experienced Trinity College London ISE II examiner (CEFR B2) giving "
    "overall feedback on a candidate's Speaking & Listening performance, based on the "
    "transcript(s) of one or more of the four parts (Topic discussion, Collaborative "
    "task, Conversation task, Independent Listening). Assess:\n"
    "- STRUCTURE: how well the candidate organised their responses (e.g. in the Topic "
    "task: presenting the topic, giving different perspectives, their own view, a "
    "conclusion).\n"
    "- GRAMMAR: accuracy of spoken language.\n"
    "- FLUENCY: naturalness, response length appropriate to the question, use of "
    "connectors, absence of excessive simplification.\n"
    "- INTERACTION: how genuinely the candidate engaged — in the Collaborative task, "
    "whether they asked good probing questions rather than closed ones; in the "
    "Conversation task, whether they kept the exchange natural rather than giving "
    "one-word answers.\n\n"
    "This candidate has 8 known recurring error types: gerunds after prepositions, "
    "modal perfects, cleft sentences, Present Perfect vs Past Simple confusion, "
    "impersonal passive voice, adverb placement, 'ultimately' vs 'lately' confusion, "
    "and overuse of 'very' before a noun instead of a stronger adjective. Watch for "
    "these WITH EXTRA ATTENTION, but only report an error if it is a genuine mistake "
    "actually present in the transcript — never invent an example to fill a quota, and "
    "never flag wording that is grammatically correct. If a part's transcript is empty "
    "or was not attempted, simply do not comment on it specifically."
)

CORRECT_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "number", "minimum": 0, "maximum": 100},
        "summary": {"type": "string"},
        "structure_comment": {"type": "string"},
        "grammar_comment": {"type": "string"},
        "fluency_comment": {"type": "string"},
        "interaction_comment": {"type": "string"},
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
    },
    "required": [
        "score",
        "summary",
        "structure_comment",
        "grammar_comment",
        "fluency_comment",
        "interaction_comment",
        "errors",
    ],
}


def _format_transcript(turns: list[ConversationTurn]) -> str:
    return "\n".join(f"{t.role.upper()}: {t.text}" for t in turns)


def correct_session(db: Session, request: SpeakingCorrectionRequest) -> SpeakingCorrectionResult:
    parts_covered = [PART_LABELS[p.task_name] for p in request.parts]
    transcript_blocks = []
    for part in request.parts:
        if not part.transcript:
            continue
        transcript_blocks.append(f"=== {PART_LABELS[part.task_name]} ===\n{_format_transcript(part.transcript)}")
    full_transcript = "\n\n".join(transcript_blocks)

    rag_query = f"Speaking {' '.join(parts_covered)} B2 fluency grammar interaction"
    retrieved = retrieve(rag_query, top_k=3)
    if retrieved:
        log_retrieval(db, rag_query, retrieved, used_in="speaking_grading")
    context_block = format_context_block(retrieved)

    user_content = (
        f"Parts included in this session: {', '.join(parts_covered)}.\n\n{full_transcript}"
        + (f"\n\n{context_block}" if context_block else "")
    )

    result = structured_completion(
        system=CORRECT_SYSTEM_PROMPT,
        user_content=user_content,
        tool_name="submit_speaking_correction",
        tool_description="Submit the marking result for the candidate's Speaking & Listening session.",
        input_schema=CORRECT_TOOL_SCHEMA,
        max_tokens=2500,
    )

    band = band_from_score(result["score"])
    session_row = PracticeSession(
        skill="speaking",
        sub_type=",".join(p.task_name for p in request.parts),
        duration_seconds=request.duration_seconds,
        score=result["score"],
        band=band,
        summary=result["summary"],
        errors=result["errors"],
        raw_response=result,
    )
    db.add(session_row)
    db.commit()
    db.refresh(session_row)

    conversation_ids = [p.conversation_id for p in request.parts if p.conversation_id]
    if conversation_ids:
        db.execute(
            update(SpeakingTranscriptTurn)
            .where(SpeakingTranscriptTurn.conversation_id.in_(conversation_ids))
            .values(session_id=session_row.id)
        )
        db.commit()

    return SpeakingCorrectionResult(
        session_id=session_row.id,
        score=result["score"],
        band=band,
        summary=result["summary"],
        structure_comment=result["structure_comment"],
        grammar_comment=result["grammar_comment"],
        fluency_comment=result["fluency_comment"],
        interaction_comment=result["interaction_comment"],
        errors=[ErrorItem(**e) for e in result["errors"]],
        created_at=session_row.created_at,
    )
