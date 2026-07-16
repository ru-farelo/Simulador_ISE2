"""Deletes every existing type="vocab" learning_item whose term (base form,
stripped of a trailing parenthetical abbreviation) matches
app/data/vocab_blacklist.py — too basic for a B2 deck. Also deletes the
matching item_progress rows so nothing is left orphaned.

Prints a full before/after count breakdown by category (thematic vs
general/NGSL) so the result can be verified directly, not just assumed.

Run from backend/:
    venv/Scripts/python.exe scripts/apply_vocab_blacklist.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, func, select  # noqa: E402

from app.core.db import SessionLocal, init_db  # noqa: E402
from app.data.vocab_blacklist import VOCAB_BLACKLIST  # noqa: E402
from app.models.db_models import ItemProgress, LearningItem  # noqa: E402


def primary_term(term: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*$", "", term).strip().lower()


def category_label(source_file: str) -> str:
    return "general" if source_file == "NGSL" else "thematic"


def main() -> None:
    init_db()
    db = SessionLocal()

    items = db.execute(select(LearningItem).where(LearningItem.type == "vocab")).scalars().all()
    matched = [it for it in items if primary_term(it.term) in VOCAB_BLACKLIST]

    print(f"Before: {len(items)} vocab items total")
    print(f"Matched for deletion: {len(matched)}\n")

    matched_ids = [it.id for it in matched]
    if matched_ids:
        db.execute(delete(ItemProgress).where(ItemProgress.item_id.in_(matched_ids)))
        db.execute(delete(LearningItem).where(LearningItem.id.in_(matched_ids)))
        db.commit()

    remaining = db.execute(select(LearningItem).where(LearningItem.type == "vocab")).scalars().all()
    by_category: dict[str, int] = {}
    for it in remaining:
        label = category_label(it.source_file)
        by_category[label] = by_category.get(label, 0) + 1

    print(f"After: {len(remaining)} vocab items total")
    for label, count in sorted(by_category.items()):
        print(f"  {label}: {count}")

    db.close()


if __name__ == "__main__":
    main()
