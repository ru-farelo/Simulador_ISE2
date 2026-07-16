"""Restores specific NGSL words that were previously deleted by
scripts/apply_vocab_blacklist.py after being removed from
app/data/vocab_blacklist.py — generates definition + translation_es +
example in one call per batch (the combined format the deck now uses)
and inserts them back into learning_items as type="vocab",
category="general", source_file="NGSL".

Processed in fixed batches of BATCH_SIZE (not one giant call for however
many words are passed in) — see app/services/batch_generation.py for why:
max_tokens now scales with batch size, and a truncated batch is
automatically retried as two smaller ones instead of crashing.

Uses the LOCAL model (Ollama), not Claude. Ollama must be running
(`ollama serve`) with the configured model pulled.

Idempotent: deletes any existing rows for these exact terms first.

Run from backend/:
    venv/Scripts/python.exe scripts/restore_ngsl_words.py however consider increase ...
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, select  # noqa: E402

from app.core.db import SessionLocal, init_db  # noqa: E402
from app.models.db_models import ItemProgress, LearningItem  # noqa: E402
from app.services.batch_generation import generate_with_retry, tokens_for_batch  # noqa: E402
from app.services.local_client import structured_completion  # noqa: E402

SOURCE_FILE = "NGSL"
BATCH_SIZE = 15

SYSTEM_PROMPT = (
    "You are creating vocabulary flashcards for a B2 English learner (CEFR) from the "
    "New General Service List (NGSL). For each word given, provide:\n"
    "1. `definition`: a concise English definition suitable for a B2 learner.\n"
    "2. `translation_es`: the single best, most natural Spanish translation for this "
    "word's common B2 sense — a short word or phrase, never a full explanation.\n"
    "3. `example`: ONE natural, complete B2-level example sentence using the word in "
    "context — not a restatement of the definition.\n"
    "Return exactly one entry per word given, in the same order, using the exact word "
    "form given as `term`."
)
TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "definition": {"type": "string"},
                    "translation_es": {"type": "string"},
                    "example": {"type": "string"},
                },
                "required": ["term", "definition", "translation_es", "example"],
            },
        }
    },
    "required": ["items"],
}


def generate_batch(words: list[str]) -> dict:
    return structured_completion(
        system=SYSTEM_PROMPT,
        user_content="Words: " + ", ".join(words),
        tool_name="submit_items",
        tool_description="Submit the generated flashcard items, one per word.",
        input_schema=TOOL_SCHEMA,
        max_tokens=tokens_for_batch(len(words)),
    )


def main(words: list[str]) -> None:
    init_db()
    db = SessionLocal()

    restored: list[dict] = []
    for i in range(0, len(words), BATCH_SIZE):
        batch = words[i : i + BATCH_SIZE]
        result = generate_with_retry(batch, generate_batch, label=f"words {i}-{i + len(batch)}")
        if result:
            restored.extend(result["items"])

    old_ids = db.execute(
        select(LearningItem.id).where(
            LearningItem.source_file == SOURCE_FILE, LearningItem.term.in_(words)
        )
    ).scalars().all()
    if old_ids:
        db.execute(delete(ItemProgress).where(ItemProgress.item_id.in_(old_ids)))
        db.execute(delete(LearningItem).where(LearningItem.id.in_(old_ids)))

    for item in restored:
        db.add(
            LearningItem(
                type="vocab",
                term=item["term"],
                definition=item["definition"],
                translation_es=item["translation_es"],
                example=item["example"],
                category="general",
                source_file=SOURCE_FILE,
            )
        )
    db.commit()

    print(f"\nRestored {len(restored)} of {len(words)} word(s):")
    for item in restored:
        print(f"  {item['term']:<12} -> {item['translation_es']:<20} | {item['example']}")

    missing = set(words) - {item["term"] for item in restored}
    if missing:
        print(f"\nMISSING (could not be generated): {sorted(missing)}")

    db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: restore_ngsl_words.py word1 word2 ...")
        sys.exit(1)
    main(sys.argv[1:])
