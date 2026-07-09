import datetime as dt

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.vector_db import VectorBase

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


class ContextChunk(VectorBase):
    """One paragraph-sized chunk of the candidate's own study material,
    ingested from /context by scripts/ingest_context.py.
    """

    __tablename__ = "context_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(500), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(Vector(EMBEDDING_DIM))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=lambda: dt.datetime.now(dt.timezone.utc)
    )
