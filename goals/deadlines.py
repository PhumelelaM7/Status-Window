from datetime import date


def compute_countdown(end_date, today):
    """Work out how many days remain until a goal's end date.

    Returns a dict describing the countdown state, or None if the
    goal has no end_date set at all. Tied to the Fire ring — this
    is meant to create a felt sense of urgency and full presence
    about the time actually remaining, not just a number.

    Possible "status" values: "upcoming" (days remain), "today"
    (the deadline is today), "overdue" (the date has passed).
    """

    # No deadline was set for this goal — nothing to count down to
    if end_date is None:
        return None

    # Subtracting two date objects gives a timedelta; .days pulls
    # out the whole number of days between them. Positive means the
    # deadline is still ahead, zero means it's today, negative
    # means it's already passed.
    days_remaining = (end_date - today).days

    if days_remaining > 0:
        status = "upcoming"
    elif days_remaining == 0:
        status = "today"
    else:
        status = "overdue"

    return {
        "days_remaining": days_remaining,
        "status": status,
    }