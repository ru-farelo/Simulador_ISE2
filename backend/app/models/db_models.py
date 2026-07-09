import datetime as dt

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
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
