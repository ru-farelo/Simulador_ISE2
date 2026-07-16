"""Builds app/data/vocab_blacklist.py: words considered too basic for a
B2 vocabulary deck (an A1/A2 learner already knows them confidently), so
they're excluded both when generating new vocab flashcards and from the
existing learning_items deck.

Seed: the first 200 words of the General Service List (Michael West,
1953 — public domain; see app/data/gsl_seed.py). Expanded via Claude
using level-appropriate judgement (not just the literal GSL) to also
catch obviously basic words the GSL's written-corpus frequency ranking
alone might miss or that could otherwise slip into topic-specific
extraction from the candidate's own PDFs (e.g. "important", "different").

Run from backend/:
    venv/Scripts/python.exe scripts/build_vocab_blacklist.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.gsl_seed import GSL_TOP_200  # noqa: E402
from app.services.anthropic_client import structured_completion  # noqa: E402

SYSTEM_PROMPT = (
    "You are curating a blacklist of English words that are too basic for a B2-level "
    "(CEFR) vocabulary deck — words a genuine A1/A2 learner already knows confidently, "
    "so a B2 candidate doesn't need dedicated flashcard practice for them.\n\n"
    "You're given a seed of ~200 core words from the historical General Service List "
    "(GSL, Michael West, 1953). Expand this into a fuller blacklist using your own "
    "level judgement, not just this literal list. Include:\n"
    "- all common function words: articles, prepositions, pronouns, conjunctions, "
    "auxiliary and modal verbs\n"
    "- the most frequent basic verbs (be, have, do, go, get, make, take, come, see, "
    "know, think, want, need, like, use, work, look, give, tell, ask, feel, seem, say, "
    "find, become, leave, put, mean, keep, let, begin, help, show, try, call, move...)\n"
    "- everyday nouns learned very early (time, day, year, people, way, thing, man, "
    "woman, child, house, school, work, life, world, money, family, home, water, food, "
    "friend, room, door, city, country, name, word, number, part...)\n"
    "- basic adjectives, INCLUDING common ones that sound 'academic' but are actually "
    "A2/B1-level, such as important, different, difficult, easy, possible, necessary, "
    "available, similar, special, sure, clear, ready, happy, sad, hot, cold, good, bad, "
    "big, small, new, old, high, long, short, young\n"
    "- basic adverbs/quantifiers/intensifiers (very, really, quite, so, too, many, "
    "much, more, most, some, any, all, always, never, often, sometimes, usually, "
    "again, also, still, just, only, even, here, there, now, then)\n"
    "- basic connectors (and, but, because, so, if, when, while, also, however, "
    "although, though)\n\n"
    "Do NOT include words that are genuinely B2-specific, topic-specific, or academic "
    "vocabulary (e.g. 'sustainable', 'algorithm', 'dilemma', 'consequence', 'disruptive', "
    "'literacy' must NOT be excluded — those are exactly the kind of word a B2 deck "
    "should keep).\n\n"
    "Return a deduplicated list of lowercase BASE word forms only (e.g. 'go', not "
    "'goes/went/going'; 'be', not 'is/are/was'). Aim for a thorough, complete list — "
    "don't hold back for length."
)

SCHEMA = {
    "type": "object",
    "properties": {
        "words": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["words"],
}


def build_blacklist() -> list[str]:
    result = structured_completion(
        system=SYSTEM_PROMPT,
        user_content="Seed words (GSL rank 1-200): " + ", ".join(GSL_TOP_200),
        tool_name="submit_blacklist",
        tool_description="Submit the expanded A1/A2 vocabulary blacklist.",
        input_schema=SCHEMA,
        max_tokens=8000,
    )
    words = {w.strip().lower() for w in result["words"] if w.strip()}
    return sorted(words)


def main() -> None:
    words = build_blacklist()
    print(f"Built blacklist with {len(words)} words\n")

    lines = []
    lines.append('"""Words considered too basic for a B2 vocabulary deck (an A1/A2')
    lines.append('learner already knows them confidently) — excluded both when generating')
    lines.append("new vocab flashcards and from the existing learning_items deck.")
    lines.append("")
    lines.append("Seed: General Service List (Michael West, 1953, public domain), first 200")
    lines.append("words by rank — see app/data/gsl_seed.py. Expanded via Claude")
    lines.append("(scripts/build_vocab_blacklist.py) using level judgement, not just the")
    lines.append("literal GSL, to also catch words like 'important' or 'different' that")
    lines.append("are A2/B1 but don't rank in the top 200 of a written-corpus frequency list.")
    lines.append("")
    lines.append("Hand-edit this file directly to add or remove words.")
    lines.append('"""')
    lines.append("")
    lines.append("VOCAB_BLACKLIST: set[str] = {")
    for i in range(0, len(words), 8):
        chunk = words[i : i + 8]
        lines.append("    " + ", ".join(repr(w) for w in chunk) + ",")
    lines.append("}")
    lines.append("")

    out_path = Path(__file__).resolve().parent.parent / "app" / "data" / "vocab_blacklist.py"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Written to {out_path}")


if __name__ == "__main__":
    main()
