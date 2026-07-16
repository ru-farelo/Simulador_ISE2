"""Extract reviewable learning items (vocab, grammar, fillers, connectors)
from the candidate's own study material, already ingested into pgvector by
ingest_context.py, into the `learning_items` SQLite table.

One Claude tool-use call per source file (not per chunk): all of a file's
chunks are joined back into one document and the model returns every
distinct, reviewable item it finds in it. This is both cheaper (15 calls
instead of ~199) and gives the model the full context of a file rather
than a single paragraph, which produces cleaner category labels.

Idempotent per source file: re-running deletes and recreates the items
(and their orphaned progress rows) for any file passed in, so editing your
notes and re-running just refreshes that file's items.

Vocab items (not grammar/filler/connector) are checked against
app/data/vocab_blacklist.py and silently dropped if too basic for B2.

Run from backend/:
    venv/Scripts/python.exe scripts/extract_learning_items.py
    venv/Scripts/python.exe scripts/extract_learning_items.py --only 5_Vocabulario_Tematico_B2.docx.pdf,1_Conectores_Fillers_B2.docx.pdf
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, select  # noqa: E402

from app.core.db import SessionLocal, init_db  # noqa: E402
from app.core.vector_db import VectorSessionLocal, init_vector_db  # noqa: E402
from app.data.vocab_blacklist import VOCAB_BLACKLIST  # noqa: E402
from app.models.db_models import ItemProgress, LearningItem  # noqa: E402


def _is_blacklisted_vocab(item: dict) -> bool:
    if item["type"] != "vocab":
        return False
    primary = re.sub(r"\s*\([^)]*\)\s*$", "", item["term"]).strip().lower()
    return primary in VOCAB_BLACKLIST
from app.models.vector_models import ContextChunk  # noqa: E402
from app.services.anthropic_client import AIServiceError, structured_completion  # noqa: E402

# Processed first so their output can be spot-checked before the rest run —
# these two have the cleanest, most structured chunks of the 15.
PRIORITY_FILES = [
    "5_Vocabulario_Tematico_B2.docx.pdf",
    "1_Conectores_Fillers_B2.docx.pdf",
]

EXTRACT_SYSTEM_PROMPT = (
    "You are building a spaced-repetition study deck for a B2-level (CEFR) English "
    "candidate preparing for the Trinity ISE II exam, from their own study notes. "
    "Read the document below and extract every distinct, genuinely reviewable item "
    "you find: individual vocabulary words or fixed expressions worth drilling, "
    "named grammar structures or rules, and spoken discourse markers (fillers or "
    "linking connectors).\n\n"
    "Rules:\n"
    "- One item per distinct word/expression/structure — never duplicate the same "
    "item twice, even if the document repeats it.\n"
    "- `type` is exactly one of: vocab, grammar, filler, connector. Use 'filler' for "
    "hesitation/stalling devices (e.g. 'well, actually...', 'to be honest...') and "
    "'connector' for logical linking words (e.g. 'however', 'having said that').\n"
    "- `term`: the word, expression, or structure name itself (short).\n"
    "- `definition`: a concise, clear explanation of its meaning or usage — in "
    "English, written for a B2 learner, grounded in what the document actually says "
    "(you may rephrase for clarity, never invent a meaning not supported by the "
    "text or common knowledge of the term).\n"
    "- `example`: ONE natural, complete B2-level English sentence that uses the term "
    "correctly in context. If the document already has a good example, you may reuse "
    "or lightly polish it; otherwise write a new original one — never copy example "
    "sentences from any other source, only from this document or your own writing.\n"
    "- `category`: a short topic label (e.g. 'work', 'environment', 'cleft sentences', "
    "'opinion fillers') to group related items later.\n"
    "- Skip pure instructional/meta text with no reviewable content (e.g. exam "
    "format explanations, word-count targets). If the document genuinely has "
    "nothing extractable, return an empty list.\n"
    "- Do not exceed roughly 40 items for a single document — prioritise the "
    "clearest, most useful ones over exhaustive coverage."
)

EXTRACT_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["vocab", "grammar", "filler", "connector"]},
                    "term": {"type": "string"},
                    "definition": {"type": "string"},
                    "example": {"type": "string"},
                    "category": {"type": "string"},
                },
                "required": ["type", "term", "definition", "example", "category"],
            },
        }
    },
    "required": ["items"],
}


def _load_sources() -> list[str]:
    vdb = VectorSessionLocal()
    try:
        rows = vdb.execute(select(ContextChunk.source).distinct()).scalars().all()
    finally:
        vdb.close()
    ordered = [s for s in PRIORITY_FILES if s in rows]
    ordered += sorted(s for s in rows if s not in PRIORITY_FILES)
    return ordered


def _load_document_text(source: str) -> str:
    vdb = VectorSessionLocal()
    try:
        rows = vdb.execute(
            select(ContextChunk.content)
            .where(ContextChunk.source == source)
            .order_by(ContextChunk.chunk_index)
        ).scalars().all()
    finally:
        vdb.close()
    return "\n\n".join(rows)


def extract_file(db, source: str) -> int:
    document_text = _load_document_text(source)
    if not document_text.strip():
        return 0

    try:
        result = structured_completion(
            system=EXTRACT_SYSTEM_PROMPT,
            user_content=f"Source file: {source}\n\n{document_text}",
            tool_name="submit_items",
            tool_description="Submit the list of extracted learning items for this document.",
            input_schema=EXTRACT_TOOL_SCHEMA,
            max_tokens=8000,
        )
    except AIServiceError as exc:
        print(f"  ERROR  {source}: {exc}")
        return -1

    items = [item for item in result.get("items", []) if not _is_blacklisted_vocab(item)]

    old_ids = db.execute(
        select(LearningItem.id).where(LearningItem.source_file == source)
    ).scalars().all()
    if old_ids:
        db.execute(delete(ItemProgress).where(ItemProgress.item_id.in_(old_ids)))
        db.execute(delete(LearningItem).where(LearningItem.source_file == source))

    for item in items:
        db.add(
            LearningItem(
                type=item["type"],
                term=item["term"],
                definition=item["definition"],
                example=item["example"],
                category=item["category"],
                source_file=source,
            )
        )
    db.commit()
    return len(items)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="Comma-separated list of source files to (re)process")
    args = parser.parse_args()

    init_db()
    init_vector_db()

    sources = _load_sources()
    if args.only:
        wanted = {s.strip() for s in args.only.split(",")}
        sources = [s for s in sources if s in wanted]
        missing = wanted - set(sources)
        if missing:
            print(f"Warning: not found in context_chunks, skipping: {missing}")

    print(f"Processing {len(sources)} source file(s)\n")

    db = SessionLocal()
    total, by_type = 0, {}
    try:
        for source in sources:
            count = extract_file(db, source)
            if count < 0:
                continue
            print(f"  OK    {count:>3} items  {source}")
            total += count
    finally:
        db.close()

    print(f"\nDone. {total} item(s) extracted across {len(sources)} file(s).")


if __name__ == "__main__":
    main()
