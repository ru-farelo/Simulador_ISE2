import datetime as dt

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PracticeSession(Base):
    """One completed practice attempt for any of the four skills.

    `errors` and `raw_response` are stored as JSON blobs rather than
    normalized tables — at this stage the only consumer is the dashboard's
    error-category aggregation, which just needs to iterate them. This will
    be revisited once the ERRANT-based classifier (block 3) needs richer,
    queryable error records.
    """

    __tablename__ = "practice_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill: Mapped[str] = mapped_column(String(20), index=True)  # reading|listening|writing|speaking
    sub_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=lambda: dt.datetime.now(dt.timezone.utc), index=True
    )
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    band: Mapped[str | None] = mapped_column(String(30), nullable=True)
    summary: Mapped[str | None] = mapped_column(String, nullable=True)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    raw_response: Mapped[dict] = mapped_column(JSON, default=dict)


class SpeakingTranscriptTurn(Base):
    """One turn (candidate or examiner) of a live Speaking conversation.

    Persisted as each turn happens (POST /speaking/{task_name}/turn), not
    only once the candidate submits the whole session for correction —
    `conversation_id` is a client-generated id for one task attempt
    (Topic/Collaborative/Conversation), so partial conversations survive
    even if the candidate never requests a correction. `session_id` starts
    NULL and is filled in by speaking_service.correct_session() once the
    matching PracticeSession is created, linking the transcript to its
    final score.
    """

    __tablename__ = "speaking_transcript_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(64), index=True)
    task_name: Mapped[str] = mapped_column(String(20))  # topic|collaborative|conversation
    turn_index: Mapped[int] = mapped_column(Integer)
    speaker: Mapped[str] = mapped_column(String(20))  # examiner|candidate
    text: Mapped[str] = mapped_column(Text)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("practice_sessions.id"), nullable=True, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=lambda: dt.datetime.now(dt.timezone.utc)
    )


class GeneratedReadingExam(Base):
    """Answer key for an AI-generated Reading exam, persisted so a candidate
    can fetch the exam and submit it later (even across a server restart)
    without the mark scheme living only in memory.
    """

    __tablename__ = "generated_reading_exams"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=lambda: dt.datetime.now(dt.timezone.utc)
    )


class RagRetrievalLog(Base):
    """Audit trail of every RAG lookup: what was searched, what came back,
    and with what similarity score — so retrieval quality can be reviewed
    later rather than trusted blindly.
    """

    __tablename__ = "rag_retrieval_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_text: Mapped[str] = mapped_column(Text)
    used_in: Mapped[str] = mapped_column(String(50))
    results: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=lambda: dt.datetime.now(dt.timezone.utc), index=True
    )


class LearningItem(Base):
    """One reviewable unit of study material — a word, a grammar structure,
    a filler/connector, or a sentence to shadow for pronunciation.

    `vocab`/`grammar`/`filler`/`connector` items come from
    scripts/extract_learning_items.py (ingested from the candidate's own
    PDFs via /context). `pronunciation` items are generated on demand by
    learning_service the first time they're needed — there's no PDF
    extraction step for them, since a shadowing target is just a fresh B2
    sentence, not something to mine from study notes.
    """

    __tablename__ = "learning_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(20), index=True)  # vocab|grammar|filler|connector|pronunciation
    term: Mapped[str] = mapped_column(String(300))
    definition: Mapped[str] = mapped_column(Text)
    example: Mapped[str] = mapped_column(Text)
    # Spanish translation, vocab items only — shown on the flashcard back
    # instead of `definition` (which stays populated but is only used as
    # the production-phase hint now, not displayed on the flashcard).
    translation_es: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100))
    source_file: Mapped[str] = mapped_column(String(500), index=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=lambda: dt.datetime.now(dt.timezone.utc)
    )
    # Grammar/filler/connector items need a freshly generated exercise
    # (prompt_sentence or opener) each time they're due — but generating
    # one costs a real Claude call, so it's cached here and reused across
    # repeated /due requests (e.g. switching tabs) until the item is
    # actually reviewed, at which point learning_service.review_item()
    # clears it so the next due cycle gets a genuinely new one.
    cached_prompt: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cached_prompt_generated_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)


class ItemProgress(Base):
    """SM-2 spaced-repetition state for one LearningItem. One row per item,
    created the first time that item is served to the candidate.
    """

    __tablename__ = "item_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("learning_items.id"), index=True, unique=True)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    due_date: Mapped[dt.date] = mapped_column(Date, default=lambda: dt.datetime.now(dt.timezone.utc).date())
    last_reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    last_result: Mapped[str | None] = mapped_column(String(20), nullable=True)  # correct|incorrect
    # The AI's explanation for the most recent review, previously generated
    # and returned to the frontend once, then discarded. Kept here so past
    # feedback can be revisited later — last attempt only, not full history,
    # same as last_result above.
    last_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_corrected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)


class ErrorReinforcement(Base):
    """One recurring-error drill: a sentence with a real mistake (or a
    generated variant of the same pattern) that the candidate must spot
    and fix themselves, plus its own SM-2 state — same mechanics as
    ItemProgress, kept separate because it's keyed to an error category
    and an optional source session rather than a LearningItem.
    """

    __tablename__ = "error_reinforcement"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    error_category: Mapped[str] = mapped_column(String(150), index=True)
    example_sentence: Mapped[str] = mapped_column(Text)  # contains the error, to be spotted & fixed
    corrected_sentence: Mapped[str] = mapped_column(Text)
    source_session_id: Mapped[int | None] = mapped_column(ForeignKey("practice_sessions.id"), nullable=True)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    due_date: Mapped[dt.date] = mapped_column(Date, default=lambda: dt.datetime.now(dt.timezone.utc).date())
    last_reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    last_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=lambda: dt.datetime.now(dt.timezone.utc)
    )
