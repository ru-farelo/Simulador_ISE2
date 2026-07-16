"""Classic SM-2 spaced repetition, shared by learning items and error
reinforcement drills. Our reviews are pass/fail (an AI or deterministic
check decides `correct`), not a self-rated 0-5 quality score, so
`quality_from_correct` maps that binary result onto the SM-2 quality
scale before running the standard algorithm.
"""

import datetime as dt

MIN_EASE_FACTOR = 1.3


def quality_from_correct(correct: bool) -> int:
    return 5 if correct else 2


def sm2_update(
    ease_factor: float, interval_days: int, repetitions: int, quality: int
) -> tuple[float, int, int]:
    """Returns the new (ease_factor, interval_days, repetitions)."""
    if quality < 3:
        repetitions = 0
        interval_days = 1
    else:
        if repetitions == 0:
            interval_days = 1
        elif repetitions == 1:
            interval_days = 6
        else:
            interval_days = round(interval_days * ease_factor)
        repetitions += 1

    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease_factor = max(MIN_EASE_FACTOR, ease_factor)

    return ease_factor, interval_days, repetitions


def next_due_date(interval_days: int, today: dt.date | None = None) -> dt.date:
    today = today or dt.datetime.now(dt.timezone.utc).date()
    return today + dt.timedelta(days=interval_days)


def sm2_soft_fail(ease_factor: float, interval_days: int, repetitions: int) -> tuple[float, int, int]:
    """A gentler penalty than the standard SM-2 quality<3 path (which
    resets repetitions to 0 and interval to 1 day). Used for grammar
    Phase 2 (free production of a structure the candidate has already
    demonstrated controlled mastery of at least twice in Phase 1) —
    failing free production shouldn't wipe out that Phase 1 progress,
    just pull the item back sooner and dent the ease factor a bit.
    """
    new_interval = max(1, interval_days // 2)
    new_ease = max(MIN_EASE_FACTOR, ease_factor - 0.15)
    return new_ease, new_interval, repetitions
