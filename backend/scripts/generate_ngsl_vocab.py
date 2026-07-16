"""Generate B2-level vocabulary flashcards for the content words in the
New General Service List (NGSL — see app/data/ngsl_words.py for license
and source), and insert them into `learning_items` as type="vocab",
category="general", source_file="NGSL". These sit alongside the
topic-specific vocab extracted from the candidate's own PDFs, and are
filterable separately in the UI via that category.

Only NOUN/PROPN/VERB/ADJ/ADV words survive scripts/filter_ngsl_pos.py's
spaCy POS filter — function words (determiners, prepositions,
conjunctions, pronouns, auxiliaries, particles, interjections, numerals)
are excluded, since they don't work as standalone vocabulary flashcards.
Words in app/data/vocab_blacklist.py (too basic for B2 — "have", "good",
"time"...) are dropped too, even though they pass the POS filter.

Idempotent: re-running deletes and recreates every item whose
source_file is "NGSL" (and its progress rows), same pattern as
extract_learning_items.py.

Uses the LOCAL model (Ollama), not Claude — this is exactly the
high-volume, low-risk generation case local_client.py exists for. Ollama
must be running (`ollama serve`) with the configured model pulled.

Run from backend/:
    venv/Scripts/python.exe scripts/generate_ngsl_vocab.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, select  # noqa: E402

from app.core.db import SessionLocal, init_db  # noqa: E402
from app.data.vocab_blacklist import VOCAB_BLACKLIST  # noqa: E402
from app.models.db_models import ItemProgress, LearningItem  # noqa: E402
from app.services.batch_generation import generate_with_retry, tokens_for_batch  # noqa: E402
from app.services.local_client import structured_completion  # noqa: E402
from scripts.filter_ngsl_pos import filter_words  # noqa: E402

SOURCE_FILE = "NGSL"
BATCH_SIZE = 20  # smaller than the Claude-era 40 — local generation is slower, keep batches modest

SYSTEM_PROMPT = (
    "You are creating vocabulary flashcards for a B2 English learner (CEFR) from the "
    "New General Service List (NGSL), a list of the highest-frequency words in general "
    "English. For each word given, provide:\n"
    "1. `definition`: a concise English definition suitable for a B2 learner, covering "
    "the word's most common, everyday sense (pick the most frequent meaning if the word "
    "is ambiguous or has multiple parts of speech).\n"
    "2. `translation_es`: the single best, most natural Spanish translation for that "
    "same sense — a short word or phrase, never a full explanation.\n"
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


def main() -> None:
    pos_filtered = [w for w, _pos in filter_words()]
    words = [w for w in pos_filtered if w.lower() not in VOCAB_BLACKLIST]
    print(
        f"POS-filtered word list: {len(pos_filtered)} words, "
        f"{len(pos_filtered) - len(words)} more dropped as too basic (blacklist), "
        f"{len(words)} remain\n"
    )

    init_db()
    db = SessionLocal()

    old_ids = db.execute(
        select(LearningItem.id).where(LearningItem.source_file == SOURCE_FILE)
    ).scalars().all()
    if old_ids:
        db.execute(delete(ItemProgress).where(ItemProgress.item_id.in_(old_ids)))
        db.execute(delete(LearningItem).where(LearningItem.source_file == SOURCE_FILE))
        db.commit()

    total = 0
    try:
        for i in range(0, len(words), BATCH_SIZE):
            batch = words[i : i + BATCH_SIZE]
            result = generate_with_retry(batch, generate_batch, label=f"words {i}-{i + len(batch)}")
            items = result["items"] if result else []

            for item in items:
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
            total += len(items)
            if items:
                print(f"  OK    {len(items):>3} words  batch {i}-{i + len(batch)}")
    finally:
        db.close()

    print(f"\nDone. {total} NGSL vocab item(s) generated out of {len(words)} filtered words.")


if __name__ == "__main__":
    main()
