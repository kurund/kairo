"""Utility functions for date and week handling."""

from datetime import datetime, timedelta


def get_current_week() -> tuple[int, int]:
    """Get current ISO week number and year.

    Returns:
        Tuple of (year, week_number)
    """
    now = datetime.now()
    iso = now.isocalendar()
    return iso.year, iso.week


def get_week_range(year: int, week: int) -> tuple[datetime, datetime]:
    """Get start and end dates for a given ISO week.

    Args:
        year: Year
        week: ISO week number (1-53)

    Returns:
        Tuple of (start_date, end_date)
    """
    # January 4th is always in week 1
    jan4 = datetime(year, 1, 4)
    week_1_start = jan4 - timedelta(days=jan4.weekday())
    week_start = week_1_start + timedelta(weeks=week - 1)
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

    return week_start, week_end


def format_week(year: int, week: int) -> str:
    """Format week for display.

    Args:
        year: Year
        week: Week number

    Returns:
        Formatted string like "2025-W45"
    """
    return f"{year}-W{week:02d}"


def parse_week(week_str: str) -> tuple[int, int]:
    """Parse week string like '45' or '2025-W45'.

    Args:
        week_str: Week string to parse

    Returns:
        Tuple of (year, week_number)

    Raises:
        ValueError: If week string format is invalid
    """
    if "-W" in week_str:
        # Format: 2025-W45
        parts = week_str.split("-W")
        if len(parts) != 2:
            raise ValueError(f"Invalid week format: {week_str}")
        return int(parts[0]), int(parts[1])
    else:
        # Just week number, use current year
        current_year, _ = get_current_week()
        return current_year, int(week_str)


def get_next_week(year: int, week: int) -> tuple[int, int]:
    """Get the next week.

    Args:
        year: Current year
        week: Current week

    Returns:
        Tuple of (next_year, next_week)
    """
    # Get the last day of current week
    _, week_end = get_week_range(year, week)
    # Add one day to get to next week
    next_week_date = week_end + timedelta(days=1)
    iso = next_week_date.isocalendar()
    return iso.year, iso.week
