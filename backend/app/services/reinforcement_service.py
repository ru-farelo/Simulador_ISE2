"""Block 2 — error reinforcement: drills built from the candidate's own
recurring mistakes, detected automatically from PracticeSession.errors
(Reading/Writing/Speaking corrections). Never populated manually.

For every real error not yet synced, one drill is created from the real
excerpt itself, plus a couple of freshly generated sentences carrying the
same mistake pattern on different topics — so the pool isn't limited to
however many times that exact error has been literally caught so far.
The candidate must spot and fix the error themselves; it's never pointed
out to them up front.
"""

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db_models import ErrorReinforcement, PracticeSession
from app.models.reinforcement import DueReinforcementItem, ReinforcementReviewRequest, ReinforcementReviewResult
from app.services.anthropic_client import structured_completion
from app.services.spaced_repetition import next_due_date, quality_from_correct, sm2_update

VARIANTS_PER_ERROR = 2

VARIANT_SYSTEM = (
    "You are creating error-correction drills for a B2 English learner (Trinity ISE "
    "II exam prep), based on one of their real recurring mistakes. Given the error "
    "category, one real example, and its correction, write NEW original B2-level "
    "sentences — on varied everyday, work, or social topics — that each naturally "
    "contain the SAME type of grammatical mistake (not exaggerated or artificial), "
    "plus the corrected version of each. Do not reuse the real example's wording or "
    "topic."
)
VARIANT_SCHEMA = {
    "type": "object",
    "properties": {
        "variants": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "sentence_with_error": {"type": "string"},
                    "corrected_sentence": {"type": "string"},
                },
                "required": ["sentence_with_error", "corrected_sentence"],
            },
        }
    },
    "required": ["variants"],
}


def _generate_variants(category: str, real_excerpt: str, real_correction: str) -> list[dict]:
    result = structured_completion(
        system=VARIANT_SYSTEM,
        user_content=(
            f"Error category: {category}\n"
            f"Real example (with the mistake): {real_excerpt}\n"
            f"Correction: {real_correction}\n\n"
            f"Write {VARIANTS_PER_ERROR} new sentences with the same mistake pattern."
        ),
        tool_name="submit_variants",
        tool_description="Submit the generated error-pattern variant sentences.",
        input_schema=VARIANT_SCHEMA,
        max_tokens=1000,
    )
    return result["variants"]


def sync_from_sessions(db: Session) -> int:
    """Scans all PracticeSession rows for errors not yet mirrored into
    error_reinforcement (matched by source_session_id + example_sentence)
    and creates a real drill + generated variants for each new one found.
    Idempotent: safe to call on every /due request.
    """
    existing = set(
        db.execute(
            select(ErrorReinforcement.source_session_id, ErrorReinforcement.example_sentence).where(
                ErrorReinforcement.source_session_id.is_not(None)
            )
        ).all()
    )

    sessions = db.execute(select(PracticeSession).where(PracticeSession.errors.is_not(None))).scalars().all()

    created = 0
    for session in sessions:
        for err in session.errors or []:
            if not isinstance(err, dict):
                continue
            excerpt = err.get("excerpt")
            category = err.get("category")
            correction = err.get("correction")
            if not excerpt or not category or not correction:
                continue
            if (session.id, excerpt) in existing:
                continue

            today = dt.datetime.now(dt.timezone.utc).date()
            db.add(
                ErrorReinforcement(
                    error_category=category,
                    example_sentence=excerpt,
                    corrected_sentence=correction,
                    source_session_id=session.id,
                    ease_factor=2.5,
                    interval_days=0,
                    repetitions=0,
                    due_date=today,
                )
            )
            created += 1

            for variant in _generate_variants(category, excerpt, correction):
                db.add(
                    ErrorReinforcement(
                        error_category=category,
                        example_sentence=variant["sentence_with_error"],
                        corrected_sentence=variant["corrected_sentence"],
                        source_session_id=None,
                        ease_factor=2.5,
                        interval_days=0,
                        repetitions=0,
                        due_date=today,
                    )
                )
                created += 1

    db.commit()
    return created


def count_due_reinforcement(db: Session) -> int:
    sync_from_sessions(db)
    today = dt.datetime.now(dt.timezone.utc).date()
    return db.execute(
        select(func.count(ErrorReinforcement.id)).where(ErrorReinforcement.due_date <= today)
    ).scalar_one()


def get_due_reinforcement(db: Session, limit: int = 5) -> list[DueReinforcementItem]:
    sync_from_sessions(db)

    today = dt.datetime.now(dt.timezone.utc).date()
    stmt = (
        select(ErrorReinforcement)
        .where(ErrorReinforcement.due_date <= today)
        .order_by(func.coalesce(ErrorReinforcement.last_reviewed_at, ErrorReinforcement.created_at))
        .limit(limit)
    )
    rows = db.execute(stmt).scalars().all()
    return [
        DueReinforcementItem(
            id=row.id,
            error_category=row.error_category,
            example_sentence=row.example_sentence,
            is_real=row.source_session_id is not None,
        )
        for row in rows
    ]


GRADE_SYSTEM = (
    "You are checking whether a B2 English learner correctly spotted and fixed a "
    "grammar mistake deliberately embedded in a sentence, without being told where it "
    "was. Compare their corrected version against the reference correction — accept "
    "any rewrite that fixes the SAME underlying error, even with different wording; "
    "reject answers that leave the mistake in place, fix a different part of the "
    "sentence, or introduce a new error."
)
GRADE_SCHEMA = {
    "type": "object",
    "properties": {"correct": {"type": "boolean"}, "feedback": {"type": "string"}},
    "required": ["correct", "feedback"],
}


def review_reinforcement(db: Session, item_id: int, request: ReinforcementReviewRequest) -> ReinforcementReviewResult:
    item = db.get(ErrorReinforcement, item_id)
    if item is None:
        raise ValueError(f"Unknown reinforcement item id: {item_id}")

    grading = structured_completion(
        system=GRADE_SYSTEM,
        user_content=(
            f"Error category: {item.error_category}\n"
            f"Original sentence (with the mistake): {item.example_sentence}\n"
            f"Reference correction: {item.corrected_sentence}\n"
            f"Candidate's corrected version: {request.answer or '(left blank)'}"
        ),
        tool_name="submit_grade",
        tool_description="Submit the grading result.",
        input_schema=GRADE_SCHEMA,
        max_tokens=300,
    )
    correct = grading["correct"]

    quality = quality_from_correct(correct)
    item.ease_factor, item.interval_days, item.repetitions = sm2_update(
        item.ease_factor, item.interval_days, item.repetitions, quality
    )
    item.due_date = next_due_date(item.interval_days)
    item.last_reviewed_at = dt.datetime.now(dt.timezone.utc)
    item.last_feedback = grading["feedback"]
    db.commit()

    return ReinforcementReviewResult(
        correct=correct,
        feedback=grading["feedback"],
        corrected_sentence=item.corrected_sentence,
        interval_days=item.interval_days,
        repetitions=item.repetitions,
        next_due_date=item.due_date,
    )
