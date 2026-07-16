"""One-off migration: populates translation_es and rewrites `example` (as a
natural usage sentence rather than a repeat of the definition) for every
existing type="vocab" learning_item — both the topic-specific ones
extracted from the candidate's own PDFs and the NGSL general-vocabulary
set. `definition` is left untouched (still used as the production-phase
hint); only translation_es and example change.

Idempotent in the sense that re-running just overwrites translation_es/
example again with a fresh pass — safe to re-run, though normally only
needed once.

Uses the LOCAL model (Ollama), not Claude. Ollama must be running
(`ollama serve`) with the configured model pulled.

Run from backend/:
    venv/Scripts/python.exe scripts/regenerate_vocab_translation.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.db import SessionLocal, init_db  # noqa: E402
from app.models.db_models import LearningItem  # noqa: E402
from app.services.batch_generation import generate_with_retry, tokens_for_batch  # noqa: E402
from app.services.local_client import structured_completion  # noqa: E402

BATCH_SIZE = 20  # smaller than the Claude-era 40 — local generation is slower, keep batches modest

SYSTEM_PROMPT = (
    "You are preparing bilingual (English/Spanish) vocabulary flashcards for a "
    "Spanish-speaking B2 English learner. For each English word or phrase below, "
    "given its existing English definition for disambiguation, provide:\n"
    "1. `translation_es`: the single best, most natural Spanish translation for THIS "
    "specific sense of the word (as used in the given definition) — a short word or "
    "phrase (e.g. 'sin embargo', 'sostenible'), never a full explanation.\n"
    "2. `example`: ONE new, natural, complete B2-level English sentence that uses the "
    "term correctly in context — a real usage example, NOT a restatement of the "
    "definition and NOT a translation.\n"
    "Return exactly one entry per item_id given, in the same order."
)
TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "integer"},
                    "translation_es": {"type": "string"},
                    "example": {"type": "string"},
                },
                "required": ["item_id", "translation_es", "example"],
            },
        }
    },
    "required": ["items"],
}


def generate_batch(items: list[LearningItem]) -> dict:
    listing = "\n".join(
        f"[{it.id}] Term: {it.term}\nDefinition: {it.definition}" for it in items
    )
    return structured_completion(
        system=SYSTEM_PROMPT,
        user_content=listing,
        tool_name="submit_translations",
        tool_description="Submit the Spanish translation and new example sentence per item.",
        input_schema=TOOL_SCHEMA,
        max_tokens=tokens_for_batch(len(items)),
    )


def main() -> None:
    init_db()
    db = SessionLocal()

    items = db.execute(select(LearningItem).where(LearningItem.type == "vocab")).scalars().all()
    print(f"Found {len(items)} vocab item(s) to regenerate\n")

    total = 0
    try:
        for i in range(0, len(items), BATCH_SIZE):
            batch = items[i : i + BATCH_SIZE]
            result = generate_with_retry(batch, generate_batch, label=f"items {i}-{i + len(batch)}")
            results = {r["item_id"]: r for r in result["items"]} if result else {}

            updated = 0
            for it in batch:
                r = results.get(it.id)
                if not r:
                    continue
                it.translation_es = r["translation_es"]
                it.example = r["example"]
                updated += 1
            db.commit()
            total += updated
            if updated:
                print(f"  OK    {updated:>3} items  batch {i}-{i + len(batch)}")
    finally:
        db.close()

    print(f"\nDone. {total} vocab item(s) updated with translation_es + new example.")


if __name__ == "__main__":
    main()
