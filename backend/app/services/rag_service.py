"""Retrieval over the candidate's own study material (ingested from
/context by scripts/ingest_context.py). Degrades gracefully to "no
context" if the vector DB isn't reachable — RAG is an enhancement to
grading, not a hard dependency for it.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.vector_db import VectorSessionLocal
from app.models.db_models import RagRetrievalLog
from app.models.vector_models import ContextChunk
from app.services.embeddings import embed_query


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    if not query or not query.strip():
        return []

    try:
        query_embedding = embed_query(query)
    except Exception:
        return []

    vdb = VectorSessionLocal()
    try:
        distance = ContextChunk.embedding.cosine_distance(query_embedding).label("distance")
        stmt = (
            select(ContextChunk.source, ContextChunk.chunk_index, ContextChunk.content, distance)
            .order_by(distance)
            .limit(top_k)
        )
        rows = vdb.execute(stmt).all()
    except Exception:
        # Vector DB not running / not yet ingested — fail open, no RAG context.
        return []
    finally:
        vdb.close()

    return [
        {
            "source": row.source,
            "chunk_index": row.chunk_index,
            "content": row.content,
            "score": round(1 - row.distance, 4),
        }
        for row in rows
    ]


def format_context_block(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    lines = ["Relevant excerpts from the candidate's own study material (use only if genuinely relevant):"]
    for chunk in chunks:
        snippet = chunk["content"][:600]
        lines.append(f"- [{chunk['source']}] {snippet}")
    return "\n".join(lines)


def log_retrieval(db: Session, query: str, results: list[dict], used_in: str) -> None:
    db.add(RagRetrievalLog(query_text=query, used_in=used_in, results=results))
    db.commit()
