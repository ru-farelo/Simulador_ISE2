"""Schemas for the daily practice module: spaced-repetition drills over
vocabulary, grammar structures, fillers/connectors, and pronunciation
shadowing, extracted from the candidate's own study material (or, for
pronunciation, generated fresh) and reviewed via SM-2.
"""

import datetime as dt
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

LearningItemType = Literal["vocab", "grammar", "filler", "connector", "pronunciation"]


class DueVocabItem(BaseModel):
    item_id: int
    type: Literal["vocab"] = "vocab"
    category: str
    phase: Literal["flashcard", "production"]
    # flashcard phase (first time the item is seen, repetitions == 0):
    # shown fully, candidate just self-rates — no writing required yet.
    term: str | None = None
    translation_es: str | None = None
    example: str | None = None
    # production phase (repetitions >= 1): gapped sentence, candidate writes the term.
    sentence: str | None = None  # gapped sentence — target term replaced with a blank
    hint: str | None = None  # definition, shown as a hint


class DueGrammarItem(BaseModel):
    item_id: int
    type: Literal["grammar"] = "grammar"
    category: str
    structure: str  # target structure name, e.g. "Cleft sentences"
    hint: str  # definition
    prompt_sentence: str  # freshly generated simple sentence to transform
    instructions: str


class DueFillerItem(BaseModel):
    item_id: int
    type: Literal["filler", "connector"]
    category: str
    target: str  # the filler/connector phrase itself
    hint: str  # definition
    opener: str  # freshly generated argument opener
    time_limit_seconds: int = 15


class DuePronunciationItem(BaseModel):
    item_id: int
    type: Literal["pronunciation"] = "pronunciation"
    category: str
    sentence: str  # target sentence to shadow
    tip: str  # pronunciation focus tip


DueItem = Annotated[
    Union[DueVocabItem, DueGrammarItem, DueFillerItem, DuePronunciationItem],
    Field(discriminator="type"),
]


class LearningReviewRequest(BaseModel):
    answer: str = ""
    # Echoed back by the frontend for types whose exercise text is generated
    # fresh each time (grammar's prompt_sentence, filler/connector's
    # opener) rather than stored on the item — vocab and pronunciation
    # don't need it, their target is derivable from the item itself.
    prompt: str | None = None
    # Set instead of `answer` for a vocab item in its flashcard phase —
    # the candidate just self-rates rather than writing anything, so
    # there's nothing for the AI to grade.
    self_rating: Literal["known", "unknown"] | None = None


class LearningReviewResult(BaseModel):
    correct: bool
    feedback: str
    corrected_answer: str | None = None
    interval_days: int
    repetitions: int
    next_due_date: dt.date
