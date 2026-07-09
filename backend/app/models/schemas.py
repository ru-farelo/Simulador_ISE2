import datetime as dt

from pydantic import BaseModel


class ErrorItem(BaseModel):
    category: str
    excerpt: str
    correction: str
    explanation: str


class SkillProgress(BaseModel):
    sessions: int
    avg_score: float | None


class DayActivity(BaseModel):
    date: dt.date
    skills_practiced: list[str]


class ErrorCategoryCount(BaseModel):
    category: str
    count: int


class DashboardSummary(BaseModel):
    streak_days: int
    weekly_activity: list[DayActivity]
    skill_progress: dict[str, SkillProgress]
    top_error_categories: list[ErrorCategoryCount]
    total_sessions: int
