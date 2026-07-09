"""Schemas for the Speaking & Listening module: a single 20-minute session
made of four parts — Topic discussion, Collaborative task, Conversation,
and Independent Listening — matching the real Trinity ISE II structure.
"""

import datetime as dt
from typing import Literal

from pydantic import BaseModel

from app.models.schemas import ErrorItem

Role = Literal["examiner", "candidate"]
SpeakingTaskName = Literal["topic", "collaborative", "conversation"]
PartName = Literal["topic", "collaborative", "conversation", "listening"]


class ConversationTurn(BaseModel):
    role: Role
    text: str


class SpeakingTurnRequest(BaseModel):
    history: list[ConversationTurn]
    context: dict = {}


class SpeakingTurnResponse(BaseModel):
    examiner_text: str
    task_complete: bool


class ListeningPassage(BaseModel):
    id: str
    source: Literal["fixed", "generated"]
    topic: str
    text: str
    general_question: str
    detail_question: str


class SpeakingPart(BaseModel):
    task_name: PartName
    transcript: list[ConversationTurn]


class SpeakingCorrectionRequest(BaseModel):
    parts: list[SpeakingPart]
    duration_seconds: int


class SpeakingCorrectionResult(BaseModel):
    session_id: int
    score: float
    band: str
    summary: str
    structure_comment: str
    grammar_comment: str
    fluency_comment: str
    interaction_comment: str
    errors: list[ErrorItem]
    created_at: dt.datetime
