"""POS-tags every word in NGSL_TOP_500 with spaCy and filters it down to
content words worth drilling as vocabulary flashcards.

Excluded POS tags: DET, ADP, CCONJ, SCONJ, PRON, AUX, PART, INTJ, NUM.
Included POS tags: NOUN, PROPN, VERB, ADJ, ADV.

Each word is tagged in isolation (single-token document) since NGSL
entries are bare lemmas with no sentence context — spaCy still assigns
its default/most-frequent POS for the token in that case.

Run from backend/:
    venv/Scripts/python.exe scripts/filter_ngsl_pos.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import spacy  # noqa: E402

from app.data.ngsl_words import NGSL_TOP_500  # noqa: E402

EXCLUDED_POS = {"DET", "ADP", "CCONJ", "SCONJ", "PRON", "AUX", "PART", "INTJ", "NUM"}
INCLUDED_POS = {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}


def filter_words() -> list[tuple[str, str]]:
    nlp = spacy.load("en_core_web_sm")
    kept: list[tuple[str, str]] = []
    for doc in nlp.pipe(NGSL_TOP_500):
        if len(doc) == 0:
            continue
        pos = doc[0].pos_
        word = doc[0].text
        if pos in INCLUDED_POS:
            kept.append((word, pos))
    return kept


if __name__ == "__main__":
    kept = filter_words()
    print(f"Kept {len(kept)} of {len(NGSL_TOP_500)} words.\n")
    print("First 30 that pass the filter:")
    for word, pos in kept[:30]:
        print(f"  {word:<20} {pos}")
