import datetime as dt
from collections import Counter

from sqlalchemy.orm import Session

from app.models.db_models import PracticeSession
from app.models.schemas import DashboardSummary, DayActivity, ErrorCategoryCount, SkillProgress

# "listening" isn't a separate skill bucket: Independent Listening is graded
# together with the other Speaking & Listening parts under skill="speaking".
SKILLS = ["reading", "writing", "speaking"]


def _compute_streak(session_dates: set[dt.date], today: dt.date) -> int:
    cursor = today if today in session_dates else today - dt.timedelta(days=1)
    streak = 0
    while cursor in session_dates:
        streak += 1
        cursor -= dt.timedelta(days=1)
    return streak


def get_summary(db: Session) -> DashboardSummary:
    sessions = db.query(PracticeSession).all()
    today = dt.datetime.now(dt.timezone.utc).date()

    session_dates = {s.created_at.date() for s in sessions}
    streak_days = _compute_streak(session_dates, today)

    weekly_activity = [
        DayActivity(
            date=day,
            skills_practiced=sorted({s.skill for s in sessions if s.created_at.date() == day}),
        )
        for day in (today - dt.timedelta(days=offset) for offset in range(6, -1, -1))
    ]

    skill_progress: dict[str, SkillProgress] = {}
    for skill in SKILLS:
        scores = [s.score for s in sessions if s.skill == skill and s.score is not None]
        skill_count = sum(1 for s in sessions if s.skill == skill)
        skill_progress[skill] = SkillProgress(
            sessions=skill_count,
            avg_score=(sum(scores) / len(scores)) if scores else None,
        )

    error_counter: Counter[str] = Counter()
    for s in sessions:
        for err in s.errors or []:
            category = err.get("category") if isinstance(err, dict) else None
            if category:
                error_counter[category] += 1
    top_error_categories = [
        ErrorCategoryCount(category=category, count=count)
        for category, count in error_counter.most_common(5)
    ]

    return DashboardSummary(
        streak_days=streak_days,
        weekly_activity=weekly_activity,
        skill_progress=skill_progress,
        top_error_categories=top_error_categories,
        total_sessions=len(sessions),
    )
