from datetime import timedelta, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Quest, DaySchedule
from .forms import QuestForm
from .scheduling import compute_schedule, compute_streak, compute_progress


def today_schedule(request, year=None, month=None, day=None):
    """
    Show all quests scheduled for a given day, in computed order.

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

    # Whether the page currently being viewed is actually today,
    # not some past or future date — used in the template and
    # available for any logic that should only apply to today
    is_today_view = viewed_date == timezone.localdate()

    # Quest's Meta.ordering already sorts by scheduled_date, order
    quests = Quest.objects.filter(scheduled_date=viewed_date)

    # Run our pure scheduling logic to get computed start/end times
    schedule_rows = compute_schedule(
        quests, day_schedule.start_time
    )

    # Compute today's progress (scheduled vs completed minutes)
    # from the same quests queryset used for the schedule.
    progress = compute_progress(quests)

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
        "progress": progress,
        "streak": streak,
        "previous_date": previous_date,
        "next_date": next_date,
        "is_today": is_today_view,
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

        # If the day is already cleared, treat this as "undo" -
        # always allowed, regardless of completion state
        if day_schedule.is_cleared:
            day_schedule.is_cleared = False
            day_schedule.save()
            return redirect("today_schedule")

        # Check whether every enabled quest for today is completed.
        # .exclude() removes disabled quests from consideration;
        # .filter(is_completed=False) then finds anything left
        # undone. If nothing matches, everything's done.
        incomplete_count = Quest.objects.filter(
            scheduled_date=today,
            is_enabled=True,
            is_completed=False,
        ).count()

        if incomplete_count == 0:
            day_schedule.is_cleared = True
            day_schedule.save()

        # If incomplete_count > 0, we simply don't clear - the
        # template will show a message explaining why, based on
        # is_cleared staying False

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


def toggle_quest_enabled(request, quest_id):
    """
    Toggle a single quest's is_enabled flag on or off.

    A disabled quest stays in the database and is still visible on
    the schedule, but doesn't take up time in compute_schedule() or
    count toward compute_progress()'s totals - useful for a quest
    you're skipping today without deleting it outright.
    """

    # Only allow this action via POST - same safety pattern as
    # clear_day and toggle_quest_complete.
    if request.method == "POST":
        quest = get_object_or_404(Quest, id=quest_id)

        quest.is_enabled = not quest.is_enabled
        quest.save()

        # Redirect back to whichever day this quest belongs to.
        return redirect(
            "today_schedule_dated",
            year=quest.scheduled_date.year,
            month=quest.scheduled_date.month,
            day=quest.scheduled_date.day,
        )
    return redirect("today_schedule")


def toggle_reschedule(request):
    """Toggle today's DaySchedule.reschedule_enabled flag on or off.

    This only ever applies to the actual current day, not whatever
    day is being viewed — "reschedule from now" only makes sense
    relative to the real current time.
    """

    if request.method == "POST":
        today = timezone.localdate()

        day_schedule, _ = DaySchedule.objects.get_or_create(date=today)

        day_schedule.reschedule_enabled = not day_schedule.reschedule_enabled
        day_schedule.save()

    return redirect("today_schedule")


def reschedule_quest(request, quest_id):
    """
    Move a single quest to a different date.

    Rather than snapping automatically to "now", the user picks
    exactly which quest to move and what what date to move it to. The
    quest is placed at the end of the target day's order, same as
     a freshly added quest would be.
    """

    quest = get_object_or_404(Quest, id=quest_id)

    if request.method == "POST":
        new_date_str = request.POST.get("new_date")
        new_time_str = request.POST.get("new_time")

        if new_date_str:
            # Convert the submitted sate string (e.g "2026-08-25")
            # into an actual date onject. datetime.scripttime parses
            # text into a datetime; date()  then drops the time
            # portion, since we only need the date part
            new_date =datetime.strptime(
                new_date_str, "%Y-%m-%d"
            ).date()
            new_time = datetime.strptime(
                new_time_str, "%H:%M"
            ).time()

            quest.scheduled_date = new_date
            quest.start_time = new_time

            # Pin the quest to this exact time - this is what
            # compute_schedule() actually reads when placing it
            quest.anchor_time = new_time

            # Rescheduling a quest also un-fails it, since the user
            # is actively giving it a new place on the schedule
            quest.is_failed = False

            # Find the highest order value already used on the
            # target date, so the moved quest lands at the end of 
            # that day's list
            existing = Quest.objects.filter(
                scheduled_date=new_date
            ).exclude(id=quest.id).order_by("-order").first()

            quest.order = (existing.order + 1) if existing else 0
            quest.save()

        return redirect(
            "today_schedule_dated",
            year=quest.scheduled_date.year,
            month=quest.scheduled_date.month,
            day=quest.scheduled_date.day,
        )
    # GET request: show a small form asking which date to move to
    return render(
        request, "quests/reschedule_quest.html", {"quest": quest}
    )


def mark_quest_failed(request, quest_id):
    """
    Permanently mark a quest as failed.

    Called when the user dismisses the "you missed this" prompt
    without reschuling. A failed quest stays visible (greyed out)
    but no longer counts as something still to complete.
    """

    if request.method == "POST":
        quest = get_object_or_404(Quest, id=quest_id)

        # Only mark as failed if it isn't already completed - a
        # quest that was actually finished should never flip to
        # failed, even if this got called by mistake
        if not quest.is_completed:
            quest.is_failed = True
            quest.save()

    # Return a tiny JSON response rather than redirecting, since
    # this will be called from JS in the background (via
    # fetch), not from a normal page investigation
    from django.http import JsonResponse
    return JsonResponse({"status": "ok"})


def update_quest_notes(request, quest_id):
    """
    Save a quest's notes text.

    Uses the POST-only safety pattern as our other quest
    actions. Redirects back to whichever day the quest belongs to.
    """

    if request.method == "POST":
        quest = get_object_or_404(Quest, id=quest_id)

        # .get() with a default of "" avoids a crash if the notes
        # field was somehow submitted empty or missing entirely
        quest.notes = request.POST.get("notes", "")
        quest.save()

        return redirect(
            "today_schedule_dated",
            year=quest.scheduled_date.year,
            month=quest.scheduled_date.month,
            day=quest.scheduled_date.day,
        )

    return redirect("today_schedule")


def update_day_notes(request, year, month, day):
    """
    Save the general notes for a specefic day.

    Unlike  quest notes, this always operates on a specefic date
    passed in via the URL - matching how the schedule page itself
    can show any day, not just today.
    """

    if request.method == "POST":
        viewed_date = timezone.datetime(
            year=year, month=month, day=day
        ).date()

        day_schedule, _ = DaySchedule.objects.get_or_create(
            date=viewed_date
        )

        day_schedule.notes = request.POST.get("notes", "")
        day_schedule.save()

        return redirect(
            "today_schedule_dated",
            year=viewed_date.year,
            month=viewed_date.month,
            day=viewed_date.day,
        )

    return redirect("today_schedule")


def set_start_time(request, year, month, day):
    """Set a day's start time to one of a few quick preset values.

    Used by the quick-select buttons (09:00 / 09:30 / 10:00) next
    to the Start Time field, as a faster alternative to typing.
    """

    # Only allow this action via POST — same safety pattern used
    # by every other action view in this file
    if request.method == "POST":
        # Rebuild the actual date being viewed from the URL's
        # year/month/day parts
        viewed_date = timezone.datetime(
            year=year, month=month, day=day
        ).date()

        # The submitted preset time, e.g. "09:30", sent by whichever
        # quick-select button was clicked
        new_time_str = request.POST.get("start_time")

        if new_time_str:
            # Parse the "HH:MM" text into a real time object
            new_time = datetime.strptime(
                new_time_str, "%H:%M"
            ).time()

            # Fetch (or create) that day's DaySchedule row, then
            # update its start_time to the chosen preset
            day_schedule, _ = DaySchedule.objects.get_or_create(
                date=viewed_date
            )
            day_schedule.start_time = new_time
            day_schedule.save()

        # Send the user back to the same day's page so they see
        # the updated start time and recalculated schedule
        return redirect(
            "today_schedule_dated",
            year=viewed_date.year,
            month=viewed_date.month,
            day=viewed_date.day,
        )

    # If reached via GET somehow, just send back to today
    return redirect("today_schedule")


def start_my_day(request):
    """
    Commit to starting today, capturing the real current time.

    This only ever applies to the actual current day - starting a
    past or future day wouldn't make sense, since the whole point
    is capturing the real moment the user began. Once set,
    day_started and started_time are treated as locked; this view is
    the only place that ever sets them.
    """

    if request.method == "POST":
        today = timezone.localdate()

        day_schedule, _ = DaySchedule.objects.get_or_create(date=today)

        # Only act if the day hasn't already been started - this
        # gaurds against the button somehow being pressed twice,
        # which would otherwise silently overwrite the original
        # Commitment time
        if not day_schedule.day_started:
            day_schedule.start_time = timezone.localtime().time()
            day_schedule.day_started = True
            day_schedule.save()

    return redirect("today_schedule")


def unlink_quest_from_goal(request, quest_id):
    """
    Remove a quest's link to its goal, without deleting the quest.
    
    The quest stays exactly where it is on the schedule day - it
    just becomes a plain, goal-less quest afterward.
    """

    if request.method == "POST":
        quest = get_object_or_404(Quest, id=quest_id)

        # Remember which goal it was linked to, so we can redirect
        # back to that goal's detail page afterward
        goal_id = quest.goal_id

        quest.goal = None
        quest.save()

        if goal_id:
            return redirect("goal_detail", goal_id=goal_id)

    return redirect("today_schedule")