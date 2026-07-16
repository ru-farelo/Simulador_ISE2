"""Daily practice: serves due spaced-repetition items as active-production
exercises (never multiple choice) and grades reviews to update SM-2 state.

Vocab and pronunciation exercises are built deterministically from the
stored item (no extra AI call needed just to fetch /due). Grammar and
filler/connector exercises need a fresh prompt sentence — the point is
testing whether the structure/expression has been internalised, not
memorising one canonical example — but generating one is a real AI call,
so it's cached on the item (see _fill_prompt_cache) and reused across
repeated /due requests until the item is actually reviewed.

Model routing: generating those practice prompts is exactly the
high-volume, low-risk case the local model (Ollama) is for — see
local_client.py — so _generate_grammar_prompts/_generate_filler_prompts
use it. Grading the candidate's actual answer (_grade_vocab, _grade_
grammar, _grade_filler, _grade_pronunciation) stays on Claude via
anthropic_client.py: that's feedback the candidate reads and trusts, not
low-stakes drill content.
"""

import datetime as dt
import difflib
import re
from collections.abc import Callable

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.db_models import ItemProgress, LearningItem
from app.models.learning import (
    DueFillerItem,
    DueGrammarItem,
    DueItem,
    DuePronunciationItem,
    DueVocabItem,
    LearningReviewRequest,
    LearningReviewResult,
)
from app.services.anthropic_client import structured_completion
from app.services.batch_generation import generate_with_retry, tokens_for_batch
from app.services.local_client import structured_completion as local_structured_completion
from app.services.spaced_repetition import next_due_date, quality_from_correct, sm2_update

# --------------------------------------------------------------- helpers

def _today() -> dt.date:
    return dt.datetime.now(dt.timezone.utc).date()


def _primary_term(term: str) -> str:
    """Strips a trailing parenthetical abbreviation, e.g. 'artificial
    intelligence (AI)' -> 'artificial intelligence', so gap-fill matching
    targets the phrase actually likely to appear in the example sentence.
    """
    return re.sub(r"\s*\([^)]*\)\s*$", "", term).strip()


def _make_gap_sentence(example: str, term: str) -> str:
    primary = _primary_term(term)
    pattern = re.compile(re.escape(primary), re.IGNORECASE)
    if pattern.search(example):
        return pattern.sub("_____", example, count=1)
    # Term not found verbatim (e.g. the model paraphrased) — fall back to a
    # cloze built from the definition-free example, blank at the end.
    return f"{example}\n\n(Write a sentence of your own using this word/phrase instead: _____ )"


def count_due_items(db: Session, item_type: str) -> int:
    """Lightweight count for the planner — never triggers pronunciation
    generation or grammar/filler prompt generation, unlike get_due_items.
    """
    today = _today()
    stmt = (
        select(func.count(LearningItem.id))
        .select_from(LearningItem)
        .outerjoin(ItemProgress, ItemProgress.item_id == LearningItem.id)
        .where(LearningItem.type == item_type)
        .where(or_(ItemProgress.id.is_(None), ItemProgress.due_date <= today))
    )
    return db.execute(stmt).scalar_one()


def _fetch_due_items(
    db: Session, item_type: str, limit: int, category_filter: str | None = None
) -> list[LearningItem]:
    today = _today()
    stmt = (
        select(LearningItem)
        .outerjoin(ItemProgress, ItemProgress.item_id == LearningItem.id)
        .where(LearningItem.type == item_type)
        .where(or_(ItemProgress.id.is_(None), ItemProgress.due_date <= today))
    )
    if category_filter == "general":
        stmt = stmt.where(LearningItem.source_file == "NGSL")
    elif category_filter == "thematic":
        stmt = stmt.where(LearningItem.source_file != "NGSL")
    stmt = stmt.order_by(func.coalesce(ItemProgress.due_date, dt.date.max)).limit(limit)
    return list(db.execute(stmt).scalars().all())


# ------------------------------------------------------- prompt generation

GRAMMAR_PROMPT_SYSTEM = (
    "You are preparing grammar transformation drills for a B2 English learner "
    "(Trinity ISE II exam prep). For EACH grammar structure listed below, write one "
    "short, simple B2-level sentence (in plain/basic form, NOT already using the "
    "target structure) about an everyday, work, or social topic, plus a one-sentence "
    "instruction telling the candidate to rewrite it using that structure. Return one "
    "entry per item_id given, in the same order."
)
GRAMMAR_PROMPT_SCHEMA = {
    "type": "object",
    "properties": {
        "prompts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "integer"},
                    "text": {"type": "string"},
                    "instructions": {"type": "string"},
                },
                "required": ["item_id", "text", "instructions"],
            },
        }
    },
    "required": ["prompts"],
}

FILLER_PROMPT_SYSTEM = (
    "You are preparing spoken fluency drills for a B2 English learner (Trinity ISE II "
    "exam prep). For EACH filler/connector expression listed below, write one short "
    "opening line (1 sentence) that starts making a point on an everyday, work, or "
    "social topic, phrased so that continuing naturally would suit that expression "
    "well. Return one entry per item_id given, in the same order."
)
FILLER_PROMPT_SCHEMA = {
    "type": "object",
    "properties": {
        "prompts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "integer"},
                    "text": {"type": "string"},
                },
                "required": ["item_id", "text"],
            },
        }
    },
    "required": ["prompts"],
}


def _generate_grammar_prompts(items: list[LearningItem]) -> dict[int, dict]:
    def call(batch: list[LearningItem]) -> dict:
        listing = "\n".join(
            f"[{it.id}] Structure: {it.term}\nDefinition: {it.definition}\nExample: {it.example}"
            for it in batch
        )
        return local_structured_completion(
            system=GRAMMAR_PROMPT_SYSTEM,
            user_content=listing,
            tool_name="submit_prompts",
            tool_description="Submit one transformation prompt per grammar item.",
            input_schema=GRAMMAR_PROMPT_SCHEMA,
            max_tokens=tokens_for_batch(len(batch)),
        )

    result = generate_with_retry(items, call, label="grammar prompts")
    return {p["item_id"]: p for p in result["prompts"]} if result else {}


def _generate_filler_prompts(items: list[LearningItem]) -> dict[int, dict]:
    def call(batch: list[LearningItem]) -> dict:
        listing = "\n".join(f"[{it.id}] Expression: {it.term}\nUsage: {it.definition}" for it in batch)
        return local_structured_completion(
            system=FILLER_PROMPT_SYSTEM,
            user_content=listing,
            tool_name="submit_prompts",
            tool_description="Submit one opening line per filler/connector item.",
            input_schema=FILLER_PROMPT_SCHEMA,
            max_tokens=tokens_for_batch(len(batch)),
        )

    result = generate_with_retry(items, call, label="filler prompts")
    return {p["item_id"]: p for p in result["prompts"]} if result else {}


PRONUNCIATION_GENERATE_SYSTEM = (
    "Write short, natural spoken B2-level English sentences (8-15 words) for shadowing "
    "pronunciation practice ahead of the Trinity ISE II speaking exam — the kind of "
    "thing a candidate might actually say discussing everyday, work, or social-issue "
    "topics. For each sentence, add ONE brief pronunciation focus tip (e.g. a weak "
    "form, a linking sound, word stress, intonation) naming the specific feature worth "
    "focusing on in that sentence."
)
PRONUNCIATION_GENERATE_SCHEMA = {
    "type": "object",
    "properties": {
        "sentences": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "tip": {"type": "string"},
                    "topic": {"type": "string"},
                },
                "required": ["text", "tip", "topic"],
            },
        }
    },
    "required": ["sentences"],
}


def _ensure_pronunciation_pool(db: Session, min_count: int) -> None:
    available = len(_fetch_due_items(db, "pronunciation", limit=min_count))
    missing = min_count - available
    if missing <= 0:
        return

    result = structured_completion(
        system=PRONUNCIATION_GENERATE_SYSTEM,
        user_content=f"Write {missing} new sentence(s), each on a different topic.",
        tool_name="submit_sentences",
        tool_description="Submit the generated shadowing sentences.",
        input_schema=PRONUNCIATION_GENERATE_SCHEMA,
        max_tokens=1200,
    )
    for s in result["sentences"]:
        db.add(
            LearningItem(
                type="pronunciation",
                term=s["text"],
                definition=s["tip"],
                example=s["text"],
                category=s["topic"],
                source_file="generated",
            )
        )
    db.commit()


def _fill_prompt_cache(
    db: Session, items: list[LearningItem], generator: Callable[[list[LearningItem]], dict[int, dict]]
) -> None:
    """Generates and caches prompt_sentence/opener only for items that
    don't already have an unused one — this is the fix for the bug where
    switching tabs (or any repeated /due call) regenerated a fresh Claude
    prompt for every due item every time, even if nothing was reviewed.
    Items with a cached_prompt already present are left untouched.
    """
    needs_prompt = [it for it in items if it.cached_prompt is None]
    if not needs_prompt:
        return

    prompts = generator(needs_prompt)
    now = dt.datetime.now(dt.timezone.utc)
    for it in needs_prompt:
        if it.id in prompts:
            it.cached_prompt = prompts[it.id]
            it.cached_prompt_generated_at = now
    db.commit()


# ------------------------------------------------------------------- due

def get_due_items(
    db: Session, item_type: str, limit: int = 5, category_filter: str | None = None
) -> list[DueItem]:
    if item_type == "pronunciation":
        _ensure_pronunciation_pool(db, min_count=limit)

    items = _fetch_due_items(db, item_type, limit, category_filter)
    if not items:
        return []

    if item_type == "vocab":
        repetitions_by_id = {
            p.item_id: p.repetitions
            for p in db.execute(
                select(ItemProgress).where(ItemProgress.item_id.in_([it.id for it in items]))
            ).scalars().all()
        }
        result: list[DueVocabItem] = []
        for it in items:
            if repetitions_by_id.get(it.id, 0) == 0:
                result.append(
                    DueVocabItem(
                        item_id=it.id,
                        category=it.category,
                        phase="flashcard",
                        term=it.term,
                        translation_es=it.translation_es,
                        example=it.example,
                    )
                )
            else:
                result.append(
                    DueVocabItem(
                        item_id=it.id,
                        category=it.category,
                        phase="production",
                        sentence=_make_gap_sentence(it.example, it.term),
                        hint=it.definition,
                    )
                )
        return result

    if item_type == "grammar":
        _fill_prompt_cache(db, items, _generate_grammar_prompts)
        return [
            DueGrammarItem(
                item_id=it.id,
                category=it.category,
                structure=it.term,
                hint=it.definition,
                prompt_sentence=it.cached_prompt["text"],
                instructions=it.cached_prompt["instructions"],
            )
            for it in items
            if it.cached_prompt
        ]

    if item_type in ("filler", "connector"):
        _fill_prompt_cache(db, items, _generate_filler_prompts)
        return [
            DueFillerItem(
                item_id=it.id,
                type=it.type,  # type: ignore[arg-type]
                category=it.category,
                target=it.term,
                hint=it.definition,
                opener=it.cached_prompt["text"],
            )
            for it in items
            if it.cached_prompt
        ]

    if item_type == "pronunciation":
        return [
            DuePronunciationItem(item_id=it.id, category=it.category, sentence=it.term, tip=it.definition)
            for it in items
        ]

    raise ValueError(f"Unknown learning item type: {item_type}")


# --------------------------------------------------------------- grading

VOCAB_GRADE_SYSTEM = (
    "You are marking a single vocabulary gap-fill answer for a B2 English learner. "
    "Judge whether the candidate's word/phrase is an acceptable match for the target "
    "term — accept correct inflections (plural, verb tense), reasonable synonyms, and "
    "minor spelling slips; reject answers that are a different word or clearly wrong. "
    "Give brief, encouraging feedback in one sentence."
)
GRADE_SCHEMA = {
    "type": "object",
    "properties": {"correct": {"type": "boolean"}, "feedback": {"type": "string"}},
    "required": ["correct", "feedback"],
}

GRAMMAR_GRADE_SYSTEM = (
    "You are marking a grammar transformation exercise for a B2 English learner. They "
    "were given a simple sentence and asked to rewrite it using a specific target "
    "structure. Judge whether their rewrite correctly and grammatically uses that "
    "structure while preserving the original meaning — minor stylistic differences are "
    "fine, but the structure must actually be present and correctly formed. Always "
    "also provide one correct model rewrite, even if the candidate's answer was right."
)
GRAMMAR_GRADE_SCHEMA = {
    "type": "object",
    "properties": {
        "correct": {"type": "boolean"},
        "feedback": {"type": "string"},
        "model_rewrite": {"type": "string"},
    },
    "required": ["correct", "feedback", "model_rewrite"],
}

FILLER_GRADE_SYSTEM = (
    "You are checking whether a B2 English learner correctly used a specific "
    "filler/connector expression in their spoken continuation of an argument. Judge "
    "ONLY whether the target expression (or a natural equivalent form of it) was used, "
    "and whether it was grammatically well-placed — do NOT judge the quality or "
    "correctness of the content/opinion itself. Give brief feedback in one sentence."
)


def _grade_vocab(item: LearningItem, answer: str) -> tuple[bool, str, None]:
    result = structured_completion(
        system=VOCAB_GRADE_SYSTEM,
        user_content=f"Target term: {item.term}\nSentence with gap: {_make_gap_sentence(item.example, item.term)}\nCandidate's answer: {answer or '(left blank)'}",
        tool_name="submit_grade",
        tool_description="Submit the grading result.",
        input_schema=GRADE_SCHEMA,
        max_tokens=300,
    )
    return result["correct"], result["feedback"], None


def _grade_grammar(item: LearningItem, prompt_sentence: str, answer: str) -> tuple[bool, str, str]:
    result = structured_completion(
        system=GRAMMAR_GRADE_SYSTEM,
        user_content=(
            f"Target structure: {item.term} ({item.definition})\n"
            f"Original simple sentence: {prompt_sentence or '(not provided)'}\n"
            f"Candidate's rewrite: {answer or '(left blank)'}"
        ),
        tool_name="submit_grade",
        tool_description="Submit the grading result.",
        input_schema=GRAMMAR_GRADE_SCHEMA,
        max_tokens=400,
    )
    return result["correct"], result["feedback"], result["model_rewrite"]


def _grade_filler(item: LearningItem, opener: str, answer: str) -> tuple[bool, str, None]:
    result = structured_completion(
        system=FILLER_GRADE_SYSTEM,
        user_content=(
            f"Target expression: {item.term}\n"
            f"Argument opener given: {opener or '(not provided)'}\n"
            f"Candidate's continuation: {answer or '(left blank)'}"
        ),
        tool_name="submit_grade",
        tool_description="Submit the grading result.",
        input_schema=GRADE_SCHEMA,
        max_tokens=300,
    )
    return result["correct"], result["feedback"], None


def _grade_pronunciation(item: LearningItem, recognized: str) -> tuple[bool, str, None]:
    target = item.term.lower().strip()
    heard = (recognized or "").lower().strip()
    ratio = difflib.SequenceMatcher(None, target, heard).ratio()
    correct = ratio >= 0.8
    pct = round(ratio * 100)
    feedback = (
        f"Coincidencia con el texto reconocido: {pct}%. "
        "Esto mide si el reconocimiento de voz del navegador transcribió las mismas "
        "palabras que el objetivo — no es un análisis fonético real, así que un acento "
        "marcado o palabras cambiadas por otras que suenan parecido pueden dar falsos "
        "negativos o positivos."
    )
    return correct, feedback, None


def review_item(db: Session, item_id: int, request: LearningReviewRequest) -> LearningReviewResult:
    item = db.get(LearningItem, item_id)
    if item is None:
        raise ValueError(f"Unknown learning item id: {item_id}")

    # The prompt_sentence/opener shown to the candidate lives in
    # item.cached_prompt (see _fill_prompt_cache) — that's the source of
    # truth for grading, not the client-echoed `request.prompt`, though the
    # latter is kept as a fallback in case cached_prompt was somehow cleared
    # between fetch and review.
    cached_text = (item.cached_prompt or {}).get("text") if item.cached_prompt else None

    if item.type == "vocab" and request.self_rating is not None:
        correct = request.self_rating == "known"
        feedback = "La marcaste como conocida." if correct else "La marcaste como no conocida — se repasará pronto."
        corrected = None
    elif item.type == "vocab":
        correct, feedback, corrected = _grade_vocab(item, request.answer)
    elif item.type == "grammar":
        correct, feedback, corrected = _grade_grammar(item, cached_text or request.prompt or "", request.answer)
    elif item.type in ("filler", "connector"):
        correct, feedback, corrected = _grade_filler(item, cached_text or request.prompt or "", request.answer)
    elif item.type == "pronunciation":
        correct, feedback, corrected = _grade_pronunciation(item, request.answer)
    else:
        raise ValueError(f"Unknown learning item type: {item.type}")

    progress = db.execute(select(ItemProgress).where(ItemProgress.item_id == item_id)).scalar_one_or_none()
    if progress is None:
        progress = ItemProgress(
            item_id=item_id, ease_factor=2.5, interval_days=0, repetitions=0, due_date=_today()
        )
        db.add(progress)

    quality = quality_from_correct(correct)
    progress.ease_factor, progress.interval_days, progress.repetitions = sm2_update(
        progress.ease_factor, progress.interval_days, progress.repetitions, quality
    )
    progress.due_date = next_due_date(progress.interval_days, today=_today())
    progress.last_reviewed_at = dt.datetime.now(dt.timezone.utc)
    progress.last_result = "correct" if correct else "incorrect"
    progress.last_feedback = feedback
    progress.last_corrected_answer = corrected

    # The exercise has now been reviewed — clear the cached prompt so the
    # next due cycle for this item generates a genuinely new one instead
    # of repeating (or silently reusing a stale) sentence.
    if item.type in ("grammar", "filler", "connector"):
        item.cached_prompt = None
        item.cached_prompt_generated_at = None

    db.commit()

    return LearningReviewResult(
        correct=correct,
        feedback=feedback,
        corrected_answer=corrected,
        interval_days=progress.interval_days,
        repetitions=progress.repetitions,
        next_due_date=progress.due_date,
    )
