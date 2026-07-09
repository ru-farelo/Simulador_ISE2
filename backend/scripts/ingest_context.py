"""Ingest every PDF under CONTEXT_DIR into the pgvector store.

Run from backend/:
    venv/Scripts/python.exe scripts/ingest_context.py

Idempotent: re-running deletes and recreates the chunks for any file whose
content changed (keyed by relative path), so editing a PDF and re-running
just refreshes it rather than duplicating rows.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pypdf import PdfReader  # noqa: E402
from sqlalchemy import delete  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.vector_db import VectorSessionLocal, init_vector_db  # noqa: E402
from app.models.vector_models import ContextChunk  # noqa: E402
from app.services.chunking import chunk_paragraphs  # noqa: E402
from app.services.embeddings import embed_texts  # noqa: E402

MIN_EXTRACTED_CHARS = 50  # below this, treat the PDF as unreadable (e.g. a scanned image)


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def ingest_file(pdf_path: Path, context_root: Path, db) -> tuple[str, int]:
    relative = pdf_path.relative_to(context_root).as_posix()
    text = extract_text(pdf_path)

    if len(text.strip()) < MIN_EXTRACTED_CHARS:
        return relative, -1  # signal: skipped, likely a scanned/handwritten PDF

    chunks = chunk_paragraphs(text)
    if not chunks:
        return relative, 0

    embeddings = embed_texts(chunks)

    db.execute(delete(ContextChunk).where(ContextChunk.source == relative))
    for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
        db.add(ContextChunk(source=relative, chunk_index=idx, content=chunk_text, embedding=embedding))
    db.commit()
    return relative, len(chunks)


def main() -> None:
    settings = get_settings()
    context_root = Path(settings.context_dir).resolve()
    if not context_root.is_dir():
        print(f"CONTEXT_DIR not found: {context_root}")
        return

    print(f"Initialising vector DB ({settings.vector_db_url})...")
    init_vector_db()

    pdf_files = sorted(context_root.rglob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF(s) under {context_root}\n")

    db = VectorSessionLocal()
    processed, skipped, total_chunks = 0, 0, 0
    try:
        for pdf_path in pdf_files:
            relative, count = ingest_file(pdf_path, context_root, db)
            if count == -1:
                print(f"  SKIP  (no extractable text — likely scanned/handwritten): {relative}")
                skipped += 1
            else:
                print(f"  OK    {count:>3} chunks  {relative}")
                processed += 1
                total_chunks += count
    finally:
        db.close()

    print(f"\nDone. {processed} file(s) ingested, {total_chunks} chunk(s) total, {skipped} file(s) skipped.")


if __name__ == "__main__":
    main()
