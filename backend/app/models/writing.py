"""Schemas for Writing (Task 4 — Extended Writing): 150-180 word pieces
whose genre varies (essay, article, letter/email, review), matching the
real Trinity ISE II Reading & Writing paper.
"""

import datetime as dt
from typing import Literal

from pydantic import BaseModel

from app.models.schemas import ErrorItem

Genre = Literal["essay", "article", "letter", "review"]


class WritingPrompt(BaseModel):
    id: str
    source: Literal["fixed", "generated"]
    genre: Genre
    title: str
    instructions: str
    word_min: int = 150
    word_max: int = 180


class WritingSubmission(BaseModel):
    prompt_id: str
    genre: Genre
    title: str
    instructions: str
    text: str
    duration_seconds: int


class ModelSentence(BaseModel):
    original: str
    rewritten: str
    explanation: str


class WritingCorrectionResult(BaseModel):
    session_id: int
    word_count: int
    band: str
    summary: str
    strengths: list[str]
    errors: list[ErrorItem]
    model_sentence: ModelSentence
    created_at: dt.datetime
