"""
scheduler.py — Phase 4
Generates randomised, human-like send timestamps within the allowed window.
"""

import random
from datetime import datetime, timedelta
from config import (
    SCHEDULE_START_HOUR,
    SCHEDULE_END_HOUR,
    MIN_DELAY_MINUTES,
    MAX_DELAY_MINUTES,
    MAX_EMAILS_PER_DAY,
)


def _next_working_day_start(from_dt: datetime) -> datetime:
    """Return 10 AM on the next calendar day."""
    return (from_dt + timedelta(days=1)).replace(
        hour=SCHEDULE_START_HOUR, minute=0, second=0, microsecond=0
    )


def build_schedule(n_emails: int, start: datetime | None = None) -> list[datetime]:
    """
    Returns a list of n_emails datetime objects representing send times.
    Automatically spills into the next working day if the window fills up.
    """
    if start is None:
        now = datetime.now()
        if now.hour >= SCHEDULE_END_HOUR:
            start = _next_working_day_start(now)
        elif now.hour < SCHEDULE_START_HOUR:
            start = now.replace(hour=SCHEDULE_START_HOUR, minute=0, second=0, microsecond=0)
        else:
            delay = random.randint(MIN_DELAY_MINUTES, MAX_DELAY_MINUTES)
            start = now + timedelta(minutes=delay)

    schedule: list[datetime] = []
    current   = start
    day_count = 0

    for _ in range(n_emails):
        window_end = current.replace(
            hour=SCHEDULE_END_HOUR, minute=0, second=0, microsecond=0
        )

        if current >= window_end or day_count >= MAX_EMAILS_PER_DAY:
            current   = _next_working_day_start(current)
            day_count = 0

        schedule.append(current)
        day_count += 1

        delay   = random.randint(MIN_DELAY_MINUTES, MAX_DELAY_MINUTES)
        current = current + timedelta(minutes=delay)

    return schedule


def format_schedule(schedule: list[datetime]) -> str:
    """Pretty-print the schedule for logging."""
    lines     = []
    prev_date = None
    for i, dt in enumerate(schedule, 1):
        if dt.date() != prev_date:
            lines.append(f"\n  {dt.strftime('%A, %B %d %Y')}")
            prev_date = dt.date()
        lines.append(f"     [{i:02}] {dt.strftime('%I:%M %p')}")
    return "\n".join(lines)
