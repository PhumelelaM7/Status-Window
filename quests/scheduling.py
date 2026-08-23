from datetime import datetime, timedelta


def compute_schedule(quests, day_start_time, reschedule_from=None):
    """Work out each quest's start/end time in order.

    quests must already be sorted by `order` (Quest's Meta.ordering
    does this automatically when queried normally). Disabled quests
    are skipped when advancing the clock, but are still returned so
    the page can display them (e.g. greyed out).

    Returns a list of dicts: {"quest": quest, "start": time, "end": time}
    """

    # Convert the day's start time into total minutes since
    # midnight, so we can do simple integer math
    cursor_minutes = day_start_time.hour * 60 + day_start_time.minute

    rows = []
    for quest in quests:
        # If this quest has an anchor time, jump the cursor
        # directly to it - ignoring wherever the cascade currently
        # sits, whether that's earlier or atr than the anchor
        if quest.anchor_time is not None:
            cursor_minutes = (
                quest.anchor_time.hour * 60 + quest.anchor_time.minute
            )
            
        start_minutes = cursor_minutes

        if quest.is_enabled:
            cursor_minutes += quest.duration_minutes
            end_minutes = cursor_minutes
        else:
            end_minutes = start_minutes

        rows.append({
            "quest": quest,
            "start": _minutes_to_time(start_minutes),
            "end": _minutes_to_time(end_minutes),
        })

    return rows


def _minutes_to_time(total_minutes):
    """Convert an integer minute count into a datetime.time object,
    wrapping past midnight if the schedule runs past 24 hours."""

    total_minutes = int(total_minutes) % (24 * 60)
    hours, minutes = divmod(total_minutes, 60)
    return datetime.min.time().replace(hour=hours, minute=minutes)


def compute_streak(cleared_dates, today):
    """Count consecutive cleared days ending today, walking backward.

    cleared_dates should be a set (or any container supporting `in`)
    of date objects that have been marked cleared. If today itself
    isn't cleared yet, the streak is 0 — clearing today is what
    extends yesterday's streak by one.
    """

    # Running count of consecutive cleared days found so far
    streak = 0

    # Start checking from today and walk backward one day at a time
    cursor = today

    # Keep counting as long as each day we check was marked cleared
    while cursor in cleared_dates:
        streak += 1
        cursor -= timedelta(days=1)

    return streak


def compute_progress(quests):
    """
    Work out total scheduled minutes vs completed minutes.

    Only enabled quests count toward the total - a disabled quest
    isn't part of todays plan, so it shouldnt affect the bar.
    Returns a dict with total_minutes, completed_minutes, 
    and percent (0-100, rounded to a whole number)
    """

    total_minutes = 0
    completed_minutes = 0

    for quest in quests:
        if not quest.is_enabled or quest.is_failed:
            # Skip disabled quests entirely - they don't count
            # toward the schedule at all.
            continue

        total_minutes += quest.duration_minutes

        if quest.is_completed:
            completed_minutes += quest.duration_minutes

    # Avoid a divide-by-zero if there are no scheduled quests yet.
    if total_minutes == 0:
        percent = 0
    else:
        percent = round((completed_minutes / total_minutes) * 100)

    return {
        "total_minutes": total_minutes,
        "completed_minutes": completed_minutes,
        "percent": percent,
    }     

