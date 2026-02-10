"""
Date/time utility functions.
"""
from datetime import date, datetime, timedelta


def hebrew_date_display(d: date | None) -> str:
    """Format date for Hebrew display: DD/MM/YYYY."""
    if not d:
        return ""
    return d.strftime("%d/%m/%Y")


def days_until(target: date) -> int:
    """Days until a target date."""
    return (target - date.today()).days


def estimate_finish_date(sessions_remaining: int, sessions_per_week: int = 2) -> date:
    """Estimate course finish date based on remaining sessions."""
    days = sessions_remaining * (7 / sessions_per_week)
    return date.today() + timedelta(days=int(days))
