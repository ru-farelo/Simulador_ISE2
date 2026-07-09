import uuid

from sqlalchemy.orm import Session

from app.data.reading_exams import FIXED_EXAMS
from app.models.db_models import GeneratedReadingExam, PracticeSession
from app.models.reading_exam import (
    ExerciseResult,
    ItemFeedback,
    MatchingExerciseInternal,
    MultiSelectExerciseInternal,
    ReadingExamInternal,
    ReadingExamPublic,
    ReadingExamResult,
    ReadingExamSubmission,
    TaskResult,
    TrueFalseExerciseInternal,
)
from app.models.schemas import ErrorItem
from app.services.anthropic_client import AIServiceError, structured_completion
from app.services.grading_common import band_from_score
from app.services.rag_service import format_context_block, log_retrieval, retrieve

# --------------------------------------------------------------- fetching

def get_fixed_exam(exam_id: str | None = None) -> ReadingExamPublic:
    if exam_id:
        match = next((e for e in FIXED_EXAMS if e["id"] == exam_id), None)
        if match is None:
            raise ValueError(f"Unknown exam id: {exam_id}")
    else:
        match = FIXED_EXAMS[0]
    return ReadingExamInternal(**match).to_public()


def _load_exam_internal(db: Session, exam_id: str) -> ReadingExamInternal:
    fixed = next((e for e in FIXED_EXAMS if e["id"] == exam_id), None)
    if fixed is not None:
        return ReadingExamInternal(**fixed)

    row = db.get(GeneratedReadingExam, exam_id)
    if row is None:
        raise ValueError(f"Unknown or expired exam id: {exam_id}")
    return ReadingExamInternal(**row.payload)


# ------------------------------------------------------------- generation

GENERATE_SYSTEM_PROMPT = (
    "You are an item writer for the Trinity College London ISE II exam "
    "(CEFR B2), Reading & Writing paper. You write ORIGINAL exam sets that "
    "exactly replicate the official structure:\n"
    "Task 1 (Long Reading): one 300-450 word text in 5 numbered paragraphs, "
    "then (A) match each paragraph to its best title from 6 options (1 is a "
    "distractor), (B) find a word/phrase in the text that means the same as "
    "6 given words/phrases from the titles, (C) 5 True/False statements, "
    "(D) 5 sentences to complete with information taken almost literally "
    "from the text.\n"
    "Task 2 (Multi-text Reading): 4 short texts (A-D) on one topic, then (A) "
    "5 'which text' questions, (B) 8 statements of which exactly 5 are true, "
    "(C) 5 summary-note gaps to fill with words/phrases from the texts.\n"
    "Task 3 (Reading into Writing): 4 short texts (A-D, mixing genres like "
    "article/interview/diary/chart-description) on one topic, then (1-5) "
    "'which text' questions where letters may repeat, (6-10) 8 statements "
    "(A-H) of which exactly 5 are true.\n"
    "All answer keys must be internally consistent and verifiable purely "
    "from the texts you write."
)

_LABELLED_SCHEMA = {
    "type": "object",
    "properties": {"id": {"type": "string"}, "text": {"type": "string"}},
    "required": ["id", "text"],
}

_MATCHING_SCHEMA = {
    "type": "object",
    "properties": {
        "instructions": {"type": "string"},
        "items": {"type": "array", "items": _LABELLED_SCHEMA},
        "options": {"type": "array", "items": _LABELLED_SCHEMA},
        "allow_repeat_options": {"type": "boolean"},
        "correct": {"type": "object", "additionalProperties": {"type": "string"}},
    },
    "required": ["instructions", "items", "options", "allow_repeat_options", "correct"],
}

_TRUE_FALSE_SCHEMA = {
    "type": "object",
    "properties": {
        "instructions": {"type": "string"},
        "statements": {"type": "array", "items": _LABELLED_SCHEMA},
        "correct": {"type": "object", "additionalProperties": {"type": "boolean"}},
    },
    "required": ["instructions", "statements", "correct"],
}

_MULTI_SELECT_SCHEMA = {
    "type": "object",
    "properties": {
        "instructions": {"type": "string"},
        "options": {"type": "array", "items": _LABELLED_SCHEMA},
        "select_count": {"type": "integer"},
        "correct": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["instructions", "options", "select_count", "correct"],
}

_GAP_FILL_SCHEMA = {
    "type": "object",
    "properties": {
        "instructions": {"type": "string"},
        "items": {"type": "array", "items": _LABELLED_SCHEMA},
        "accepted_answers": {
            "type": "object",
            "additionalProperties": {"type": "array", "items": {"type": "string"}},
        },
    },
    "required": ["instructions", "items", "accepted_answers"],
}

GENERATE_EXAM_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "task1": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "paragraphs": {"type": "array", "items": _LABELLED_SCHEMA},
                "exercise_a": _MATCHING_SCHEMA,
                "exercise_b": _GAP_FILL_SCHEMA,
                "exercise_c": _TRUE_FALSE_SCHEMA,
                "exercise_d": _GAP_FILL_SCHEMA,
            },
            "required": ["title", "paragraphs", "exercise_a", "exercise_b", "exercise_c", "exercise_d"],
        },
        "task2": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "texts": {"type": "array", "items": _LABELLED_SCHEMA},
                "exercise_a": _MATCHING_SCHEMA,
                "exercise_b": _MULTI_SELECT_SCHEMA,
                "exercise_c": _GAP_FILL_SCHEMA,
            },
            "required": ["title", "texts", "exercise_a", "exercise_b", "exercise_c"],
        },
        "task3": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "texts": {"type": "array", "items": _LABELLED_SCHEMA},
                "exercise_1_5": _MATCHING_SCHEMA,
                "exercise_6_10": _MULTI_SELECT_SCHEMA,
            },
            "required": ["title", "texts", "exercise_1_5", "exercise_6_10"],
        },
    },
    "required": ["task1", "task2", "task3"],
}


def generate_exam(db: Session) -> ReadingExamPublic:
    result = structured_completion(
        system=GENERATE_SYSTEM_PROMPT,
        user_content=(
            "Write one new B2-level Reading exam set (Task 1, 2 and 3) on topics "
            "of your choice, different from bullying, emotional intelligence and "
            "family business."
        ),
        tool_name="submit_exam",
        tool_description="Submit the generated Reading exam with all three tasks and their answer keys.",
        input_schema=GENERATE_EXAM_TOOL_SCHEMA,
        max_tokens=8000,
    )

    exam_id = f"generated-{uuid.uuid4().hex[:8]}"
    payload = {"id": exam_id, "source": "generated", **result}
    exam = ReadingExamInternal(**payload)  # validates shape before persisting

    db.add(GeneratedReadingExam(id=exam_id, payload=payload))
    db.commit()

    return exam.to_public()


# ---------------------------------------------------------------- grading

def _grade_matching(label: str, exercise: MatchingExerciseInternal, answers: dict[str, str]) -> ExerciseResult:
    option_text = {o.id: o.text for o in exercise.options}
    items, correct_count = [], 0
    for item in exercise.items:
        expected = exercise.correct.get(item.id)
        is_correct = answers.get(item.id) == expected
        correct_count += is_correct
        items.append(ItemFeedback(id=item.id, correct=is_correct, expected=option_text.get(expected, expected)))
    return ExerciseResult(label=label, correct_count=correct_count, total_count=len(exercise.items), items=items)


def _grade_true_false(label: str, exercise: TrueFalseExerciseInternal, answers: dict[str, bool]) -> ExerciseResult:
    items, correct_count = [], 0
    for statement in exercise.statements:
        expected = exercise.correct.get(statement.id)
        is_correct = answers.get(statement.id) == expected
        correct_count += is_correct
        items.append(ItemFeedback(id=statement.id, correct=is_correct, expected="True" if expected else "False"))
    return ExerciseResult(label=label, correct_count=correct_count, total_count=len(exercise.statements), items=items)


def _grade_multi_select(label: str, exercise: MultiSelectExerciseInternal, selected: list[str]) -> ExerciseResult:
    correct_set, selected_set = set(exercise.correct), set(selected)
    items, correct_count = [], 0
    for option in exercise.options:
        should_select = option.id in correct_set
        is_correct = should_select == (option.id in selected_set)
        correct_count += is_correct
        items.append(ItemFeedback(id=option.id, correct=is_correct, expected="select" if should_select else "leave unselected"))
    return ExerciseResult(label=label, correct_count=correct_count, total_count=len(exercise.options), items=items)


GRADE_GAPFILL_SYSTEM_PROMPT = (
    "You are an experienced Trinity College London ISE II examiner (CEFR "
    "B2) marking short free-text answers from the Reading paper (synonym "
    "spotting, gap fills, summary completion). For each item, judge whether "
    "the candidate's answer is an acceptable paraphrase or match of the "
    "reference answer(s) — accept reasonable synonyms and minor spelling "
    "variants, reject answers that change the meaning. Separately, review "
    "the candidate's own wording across all their answers for genuine "
    "grammar mistakes (not exam correctness) and flag them as errors.\n\n"
    "This candidate has 8 known recurring error types: gerunds after "
    "prepositions, modal perfects, cleft sentences, Present Perfect vs Past "
    "Simple confusion, impersonal passive voice, adverb placement, "
    "'ultimately' vs 'lately' confusion, and overuse of 'very' before a "
    "noun instead of a stronger adjective. Watch for these WITH EXTRA "
    "ATTENTION, but only report an error if it is a genuine mistake that is "
    "actually present — never invent an example to fill a quota, never "
    "flag wording that is grammatically correct, and never include an "
    "'error' whose own correction says no change is needed. Short answers "
    "with no mistakes should simply produce no errors for that item."
)

GRADE_GAPFILL_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "item_feedback": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "unique_id": {"type": "string"},
                    "is_correct": {"type": "boolean"},
                    "comment": {"type": "string"},
                },
                "required": ["unique_id", "is_correct", "comment"],
            },
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
        "overall_comment": {"type": "string"},
    },
    "required": ["item_feedback", "errors", "overall_comment"],
}


def _collect_gapfill_items(exam: ReadingExamInternal, submission: ReadingExamSubmission) -> list[dict]:
    sources = [
        ("task1.b", "Task 1 – B (vocabulary)", exam.task1.exercise_b, submission.task1.exercise_b),
        ("task1.d", "Task 1 – D (complete the sentences)", exam.task1.exercise_d, submission.task1.exercise_d),
        ("task2.c", "Task 2 – C (summary notes)", exam.task2.exercise_c, submission.task2.exercise_c),
    ]
    collected = []
    for prefix, label, exercise, answers in sources:
        for item in exercise.items:
            collected.append(
                {
                    "unique_id": f"{prefix}:{item.id}",
                    "label": label,
                    "prompt": item.text,
                    "accepted_answers": exercise.accepted_answers.get(item.id, []),
                    "candidate_answer": answers.get(item.id, ""),
                }
            )
    return collected


def _build_gapfill_prompt(items: list[dict]) -> str:
    blocks = []
    for entry in items:
        blocks.append(
            f"[{entry['unique_id']}] {entry['label']}\n"
            f"Prompt: {entry['prompt']}\n"
            f"Reference answer(s): {', '.join(entry['accepted_answers']) or '(none provided)'}\n"
            f"Candidate's answer: {entry['candidate_answer'] or '(left blank)'}"
        )
    return "\n\n".join(blocks)


def grade_submission(db: Session, submission: ReadingExamSubmission) -> ReadingExamResult:
    exam = _load_exam_internal(db, submission.exam_id)

    task_results: list[TaskResult] = []

    # Task 1 — deterministic exercises A and C graded locally
    t1_ex_a = _grade_matching("Task 1 – A (title matching)", exam.task1.exercise_a, submission.task1.exercise_a)
    t1_ex_c = _grade_true_false("Task 1 – C (true/false)", exam.task1.exercise_c, submission.task1.exercise_c)

    # Task 2 — deterministic exercises A and B graded locally
    t2_ex_a = _grade_matching("Task 2 – A (which text)", exam.task2.exercise_a, submission.task2.exercise_a)
    t2_ex_b = _grade_multi_select("Task 2 – B (true statements)", exam.task2.exercise_b, submission.task2.exercise_b)

    # Task 3 — fully deterministic, no free text at all
    t3_ex_15 = _grade_matching("Task 3 – 1-5 (which text)", exam.task3.exercise_1_5, submission.task3.exercise_1_5)
    t3_ex_610 = _grade_multi_select("Task 3 – 6-10 (true statements)", exam.task3.exercise_6_10, submission.task3.exercise_6_10)

    gapfill_items = _collect_gapfill_items(exam, submission)

    rag_query = f"{exam.task1.title} {exam.task2.title} {exam.task3.title} B2 vocabulary grammar"
    retrieved = retrieve(rag_query, top_k=3)
    if retrieved:
        log_retrieval(db, rag_query, retrieved, used_in="reading_grading")
    context_block = format_context_block(retrieved)

    gapfill_prompt = _build_gapfill_prompt(gapfill_items)
    if context_block:
        gapfill_prompt = f"{gapfill_prompt}\n\n{context_block}"

    try:
        ai_result = structured_completion(
            system=GRADE_GAPFILL_SYSTEM_PROMPT,
            user_content=gapfill_prompt,
            tool_name="submit_gapfill_grading",
            tool_description="Submit the grading for all free-text gap-fill answers in this Reading exam.",
            input_schema=GRADE_GAPFILL_TOOL_SCHEMA,
            max_tokens=3000,
        )
    except AIServiceError:
        raise

    feedback_by_id = {f["unique_id"]: f for f in ai_result["item_feedback"]}

    def _gapfill_exercise_result(label: str, prefix: str, exercise) -> ExerciseResult:
        items, correct_count = [], 0
        for item in exercise.items:
            uid = f"{prefix}:{item.id}"
            fb = feedback_by_id.get(uid, {"is_correct": False, "comment": "Not graded."})
            correct_count += fb["is_correct"]
            items.append(ItemFeedback(id=item.id, correct=fb["is_correct"], comment=fb["comment"]))
        return ExerciseResult(label=label, correct_count=correct_count, total_count=len(exercise.items), items=items)

    t1_ex_b = _gapfill_exercise_result("Task 1 – B (vocabulary)", "task1.b", exam.task1.exercise_b)
    t1_ex_d = _gapfill_exercise_result("Task 1 – D (complete the sentences)", "task1.d", exam.task1.exercise_d)
    t2_ex_c = _gapfill_exercise_result("Task 2 – C (summary notes)", "task2.c", exam.task2.exercise_c)

    task_results = [
        TaskResult(
            task_number=1,
            title=exam.task1.title,
            exercises=[t1_ex_a, t1_ex_b, t1_ex_c, t1_ex_d],
            correct_count=sum(e.correct_count for e in [t1_ex_a, t1_ex_b, t1_ex_c, t1_ex_d]),
            total_count=sum(e.total_count for e in [t1_ex_a, t1_ex_b, t1_ex_c, t1_ex_d]),
        ),
        TaskResult(
            task_number=2,
            title=exam.task2.title,
            exercises=[t2_ex_a, t2_ex_b, t2_ex_c],
            correct_count=sum(e.correct_count for e in [t2_ex_a, t2_ex_b, t2_ex_c]),
            total_count=sum(e.total_count for e in [t2_ex_a, t2_ex_b, t2_ex_c]),
        ),
        TaskResult(
            task_number=3,
            title=exam.task3.title,
            exercises=[t3_ex_15, t3_ex_610],
            correct_count=sum(e.correct_count for e in [t3_ex_15, t3_ex_610]),
            total_count=sum(e.total_count for e in [t3_ex_15, t3_ex_610]),
        ),
    ]

    total_correct = sum(t.correct_count for t in task_results)
    total_items = sum(t.total_count for t in task_results)
    overall_score = round((total_correct / total_items) * 100, 1) if total_items else 0.0
    band = band_from_score(overall_score)
    errors = [ErrorItem(**e) for e in ai_result["errors"]]

    session_row = PracticeSession(
        skill="reading",
        sub_type=submission.exam_id,
        duration_seconds=submission.duration_seconds,
        score=overall_score,
        band=band,
        summary=ai_result["overall_comment"],
        errors=ai_result["errors"],
        raw_response={"tasks": [t.model_dump() for t in task_results], "ai": ai_result},
    )
    db.add(session_row)
    db.commit()
    db.refresh(session_row)

    return ReadingExamResult(
        session_id=session_row.id,
        overall_score=overall_score,
        band=band,
        summary=ai_result["overall_comment"],
        tasks=task_results,
        errors=errors,
        created_at=session_row.created_at,
    )
