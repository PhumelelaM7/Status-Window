from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Quest, DaySchedule
from .forms import QuestForm
from .scheduling import compute_schedule, compute_streak


def today_schedule(request, year=None, month=None, day=None):
    """Show all quests scheduled for a given day, in computed order.

    If year/month/day aren't provided (the plain "/" URL), defaults
    to today. When provided, they come from the URL as strings via
    the date converter, letting us view any past or future day.
    """

    # Work out which date this page is actually showing. date()
    # here refers to Python's built-in datetime.date, imported
    # implicitly via timezone.localdate()'s return type
    if year and month and day:
        viewed_date = timezone.datetime(
            year=year, month=month, day=day
        ).date()
    else:
        viewed_date = timezone.localdate()

    # get_or_create either fetches viewed_date's DaySchedule row, or
    # makes one with default values if it doesn't exist yet
    day_schedule, _ = DaySchedule.objects.get_or_create(date=viewed_date)

    # Quest's Meta.ordering already sorts by scheduled_date, order
    quests = Quest.objects.filter(scheduled_date=viewed_date)

    # Run our pure scheduling logic to get computed start/end times
    schedule_rows = compute_schedule(quests, day_schedule.start_time)

    # Build the set of cleared dates to feed into compute_streak
    cleared_dates = set(
        DaySchedule.objects.filter(is_cleared=True).values_list(
            "date", flat=True
        )
    )

    # Streak is always computed from actual today, not the day
    # being viewed — browsing to a past day shouldn't change it
    streak = compute_streak(cleared_dates, timezone.localdate())

    # Precompute yesterday/tomorrow so the template can just link
    # to them directly, without doing date math in the template
    # language (which is deliberately limited)
    previous_date = viewed_date - timedelta(days=1)
    next_date = viewed_date + timedelta(days=1)

    context = {
        "today": viewed_date,
        "day_schedule": day_schedule,
        "schedule_rows": schedule_rows,
        "streak": streak,
        "previous_date": previous_date,
        "next_date": next_date,
        "is_today": viewed_date == timezone.localdate(),
    }

    return render(request, "quests/today.html", context)


def add_quest(request):
    """Show a form to add a new quest, and save it on submission."""

    if request.method == "POST":
        form = QuestForm(request.POST)

        if form.is_valid():
            # Don't save to the database yet — commit=False gives us
            # the Quest object so we can set a field before saving
            quest = form.save(commit=False)

            # Find the highest existing order value for this quest's
            # date, and place the new quest one after it
            existing = Quest.objects.filter(
                scheduled_date=quest.scheduled_date
            ).order_by("-order").first()

            quest.order = (existing.order + 1) if existing else 0
            quest.save()

            return redirect("today_schedule")
    else:
        form = QuestForm()

    return render(request, "quests/add_quest.html", {"form": form})


def clear_day(request):
    """Toggle today's DaySchedule.is_cleared flag on or off."""

    # Only allow this action via POST — a GET request (like just
    # visiting a URL or a search engine crawler) should never
    # trigger a state change
    if request.method == "POST":
        today = timezone.localdate()

        # Same get_or_create pattern as today_schedule — ensures a
        # DaySchedule row exists even if this is somehow called
        # before today_schedule ever ran
        day_schedule, _ = DaySchedule.objects.get_or_create(date=today)

        # Flip the flag: cleared becomes uncleared, and vice versa
        day_schedule.is_cleared = not day_schedule.is_cleared
        day_schedule.save()

    return redirect("today_schedule")


def toggle_quest_complete(request, quest_id):
    """Toggle a single quest's is_completed flag on or off."""

    # Only allow this action via POST — same safety pattern as
    # clear_day, since this changes data rather than just showing it
    if request.method == "POST":
        # get_object_or_404 fetches the Quest by id, or shows a
        # proper "not found" page if the id doesn't exist
        quest = get_object_or_404(Quest, id=quest_id)

        quest.is_completed = not quest.is_completed

        # Stamp completed_at when marking complete, clear it again
        # if the quest is un-completed (e.g. someone clicked by
        # mistake)
        if quest.is_completed:
            quest.completed_at = timezone.now()
        else:
            quest.completed_at = None

        quest.save()

        # Redirect back to whichever day this quest belongs to,
        # not necessarily today — so completing a quest while
        # browsing a past/future day keeps you on that same day
        return redirect(
            "today_schedule_dated",
            year=quest.scheduled_date.year,
            month=quest.scheduled_date.month,
            day=quest.scheduled_date.day,
        )

    # If somehow reached via GET, just send back to today
    return redirect("today_schedule")


def move_quest(request, quest_id, direction):
    """Move a quest one position up or down in its day's order.

    direction should be the string "up" or "down". Moving works by
    swapping this quest's order value with whichever neighboring
    quest currently sits in that direction — a simple, safe way to
    reorder without needing to renumber everything else.
    """

    if request.method == "POST":
        quest = get_object_or_404(Quest, id=quest_id)

        # Get every quest on the same day, in current order, so we
        # can find this quest's immediate neighbor
        siblings = list(
            Quest.objects.filter(
                scheduled_date=quest.scheduled_date
            )
        )

        # Find this quest's position in that list
        current_index = siblings.index(quest)

        if direction == "up" and current_index > 0:
            neighbor = siblings[current_index - 1]
        elif direction == "down" and current_index < len(siblings) - 1:
            neighbor = siblings[current_index + 1]
        else:
            # Already at the top/bottom — nothing to do
            neighbor = None

        if neighbor:
            # Swap the two order values. Python lets us do this in
            # one line using tuple assignment, rather than needing
            # a temporary variable
            quest.order, neighbor.order = neighbor.order, quest.order
            quest.save()
            neighbor.save()

        return redirect(
            "today_schedule_dated",
            year=quest.scheduled_date.year,
            month=quest.scheduled_date.month,
            day=quest.scheduled_date.day,
        )

    return redirect("today_schedule")