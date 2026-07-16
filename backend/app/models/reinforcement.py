import datetime as dt

from pydantic import BaseModel


class DueReinforcementItem(BaseModel):
    id: int
    error_category: str
    example_sentence: str  # contains the error — candidate must spot & fix it themselves
    is_real: bool  # True if drawn from an actual practice session, False if a generated variant


class ReinforcementReviewRequest(BaseModel):
    answer: str


class ReinforcementReviewResult(BaseModel):
    correct: bool
    feedback: str
    corrected_sentence: str
    interval_days: int
    repetitions: int
    next_due_date: dt.date
