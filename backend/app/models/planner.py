import datetime as dt

from pydantic import BaseModel

from app.models.schemas import ErrorCategoryCount


class PlannerBlock(BaseModel):
    type: str
    label: str
    due_count: int


class PlannerToday(BaseModel):
    date: dt.date
    blocks: list[PlannerBlock]
    total_due: int
    top_error_categories: list[ErrorCategoryCount]
    suggestion: str
