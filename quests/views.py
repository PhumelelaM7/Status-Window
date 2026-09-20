"""Views for the quests app: the daily schedule, quest CRUD and
actions (complete, reorder, enable/disable, reschedule, fail,
notes), and day-level actions (clear day, start my day, day notes,
start time) — all scoped to the logged-in user via request.user.
"""

from datetime import timedelta, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Quest, DaySchedule
from .forms import QuestForm
from .scheduling import compute_schedule, compute_streak, compute_progress


@login_required
def today_schedule(request, year=None, month=None, day=None):
    """Show all quests scheduled for a given day, in computed order.

    If year/month/day aren't provided (the plain "/" URL), defaults
    to today. When provided, they come from the URL as strings via
    the date converter, letting us view any past or future day.
    Every query here is scoped to request.user so each account only
    ever sees and creates its own data.
    """

    # Work out which date this page is actually showing
    if year and month and day:
        viewed_date = timezone.datetime(
            year=year, month=month, day=day
        ).date()
    else:
        viewed_date = timezone.localdate()

    # get_or_create includes user=request.user, so each account
    # gets its own independent DaySchedule per date
    day_schedule, _ = DaySchedule.objects.get_or_create(
        date=viewed_date, user=request.user
    )

    # Whether the page currently being viewed is actually today
    is_today_view = viewed_date == timezone.localdate()

    # Filtered to this user's own quests only
    quests = Quest.objects.filter(
        scheduled_date=viewed_date, user=request.user
    )

    # Run our pure scheduling logic to get computed start/end times
    schedule_rows = compute_schedule(quests, day_schedule.start_time)

    # Compute today's progress from this user's quests only
    progress = compute_progress(quests)

    # Build the set of cleared dates, scoped to this user only —
    # someone else's streak shouldn't affect yours
    cleared_dates = set(
        DaySchedule.objects.filter(
            is_cleared=True, user=request.user
        ).values_list("date", flat=True)
    )

    # Streak is always computed from actual today, not the day
    # being viewed — browsing to a past day shouldn't change it
    streak = compute_streak(cleared_dates, timezone.localdate())

    # Precompute yesterday/tomorrow so the template can just link
    # to them directly, without doing date math in the template
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


@login_required
def add_quest(request):
    """Show a form to add a new quest, and save it on submission.

    The QuestForm is given the logged-in user so its goal dropdown
    only lists that user's own goals, and the new quest is
    explicitly assigned to request.user before saving.
    """

    if request.method == "POST":
        form = QuestForm(request.POST, user=request.user)

        if form.is_valid():
            # Don't save to the database yet — commit=False gives
            # us the Quest object so we can set fields before saving
            quest = form.save(commit=False)

            # Assign ownership to the currently logged-in user
            quest.user = request.user

            # Find the highest existing order value for this user's
            # quests on this date, so the new quest lands at the end
            existing = Quest.objects.filter(
                scheduled_date=quest.scheduled_date,
                user=request.user,
            ).order_by("-order").first()

            quest.order = (existing.order + 1) if existing else 0
            quest.save()

            return redirect("today_schedule")
    else:
        form = QuestForm(user=request.user)

    return render(request, "quests/add_quest.html", {"form": form})


@login_required
def clear_day(request):
    """Mark today cleared, but only if every enabled quest is done.

    Disabled quests don't count — they're not part of today's plan.
    If anything enabled is still incomplete, we don't clear the day;
    the template shows a hint instead. Scoped to request.user.
    """

    if request.method == "POST":
        today = timezone.localdate()

        day_schedule, _ = DaySchedule.objects.get_or_create(
            date=today, user=request.user
        )

        # If the day is already cleared, treat this as "undo" —
        # always allowed, regardless of completion state
        if day_schedule.is_cleared:
            day_schedule.is_cleared = False
            day_schedule.save()
            return redirect("today_schedule")

        # Check whether every enabled quest for today (this user
        # only) is completed
        incomplete_count = Quest.objects.filter(
            scheduled_date=today,
            user=request.user,
            is_enabled=True,
            is_completed=False,
        ).count()

        if incomplete_count == 0:
            day_schedule.is_cleared = True
            day_schedule.save()

        # If incomplete_count > 0, we simply don't clear — the
        # template explains why, based on is_cleared staying False

    return redirect("today_schedule")


@login_required
def toggle_quest_complete(request, quest_id):
    """Toggle a single quest's is_completed flag on or off.

    Filtering by user=request.user prevents one user from
    completing another user's quest, even if they guessed its ID.
    """

    if request.method == "POST":
        quest = get_object_or_404(Quest, id=quest_id, user=request.user)

        quest.is_completed = not quest.is_completed

        # Stamp completed_at when marking complete, clear it again
        # if the quest is un-completed
        if quest.is_completed:
            quest.completed_at = timezone.now()
        else:
            quest.completed_at = None

        quest.save()

        # Redirect back to whichever day this quest belongs to
        return redirect(
            "today_schedule_dated",
            year=quest.scheduled_date.year,
            month=quest.scheduled_date.month,
            day=quest.scheduled_date.day,
        )

    return redirect("today_schedule")


@login_required
def move_quest(request, quest_id, direction):
    """Move a quest one position up or down in its day's order.

    direction should be the string "up" or "down". Moving works by
    swapping this quest's order value with whichever neighboring
    quest currently sits in that direction. Siblings are limited to
    this user's own quests on the same date.
    """

    if request.method == "POST":
        quest = get_object_or_404(Quest, id=quest_id, user=request.user)

        # Only this user's quests on this date are eligible siblings
        siblings = list(
            Quest.objects.filter(
                scheduled_date=quest.scheduled_date,
                user=request.user,
            )
        )

        current_index = siblings.index(quest)

        if direction == "up" and current_index > 0:
            neighbor = siblings[current_index - 1]
        elif direction == "down" and current_index < len(siblings) - 1:
            neighbor = siblings[current_index + 1]
        else:
            neighbor = None

        if neighbor:
            # Swap the two order values via tuple assignment
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


@login_required
def toggle_quest_enabled(request, quest_id):
    """Toggle a single quest's is_enabled flag on or off.

    A disabled quest stays in the database and is still visible on
    the schedule, but doesn't take up time in compute_schedule() or
    count toward compute_progress()'s totals.
    """

    if request.method == "POST":
        quest = get_object_or_404(Quest, id=quest_id, user=request.user)

        quest.is_enabled = not quest.is_enabled
        quest.save()

        return redirect(
            "today_schedule_dated",
            year=quest.scheduled_date.year,
            month=quest.scheduled_date.month,
            day=quest.scheduled_date.day,
        )

    return redirect("today_schedule")


@login_required
def reschedule_quest(request, quest_id):
    """Move a single quest to a different date and/or start time.

    Setting anchor_time (rather than just start_time) is what
    actually makes the new time "stick" in compute_schedule().
    """

    quest = get_object_or_404(Quest, id=quest_id, user=request.user)

    if request.method == "POST":
        new_date_str = request.POST.get("new_date")
        new_time_str = request.POST.get("new_time")

        if new_date_str and new_time_str:
            # Parse the submitted "YYYY-MM-DD" and "HH:MM" strings
            # into real date/time objects
            new_date = datetime.strptime(
                new_date_str, "%Y-%m-%d"
            ).date()
            new_time = datetime.strptime(
                new_time_str, "%H:%M"
            ).time()

            quest.scheduled_date = new_date
            quest.start_time = new_time

            # Pin the quest to this exact time — this is what
            # compute_schedule() actually reads when placing it
            quest.anchor_time = new_time

            # Rescheduling a quest also un-fails it, since the user
            # is actively giving it a new place on the schedule
            quest.is_failed = False

            # Find the highest order value already used on the
            # target date (for this user), so the moved quest lands
            # at the end of that day's list
            existing = Quest.objects.filter(
                scheduled_date=new_date,
                user=request.user,
            ).exclude(id=quest.id).order_by("-order").first()

            quest.order = (existing.order + 1) if existing else 0
            quest.save()

        return redirect(
            "today_schedule_dated",
            year=quest.scheduled_date.year,
            month=quest.scheduled_date.month,
            day=quest.scheduled_date.day,
        )

    # GET request: show a small form asking which date/time to move to
    return render(
        request, "quests/reschedule_quest.html", {"quest": quest}
    )


@login_required
def mark_quest_failed(request, quest_id):
    """Permanently mark a quest as failed.

    Called when the user dismisses the "you missed this" prompt
    without rescheduling. A failed quest stays visible (greyed out)
    but no longer counts as something still to complete. Returns
    JSON since this is called from JavaScript in the background.
    """

    if request.method == "POST":
        quest = get_object_or_404(Quest, id=quest_id, user=request.user)

        # Only mark as failed if it isn't already completed
        if not quest.is_completed:
            quest.is_failed = True
            quest.save()

    return JsonResponse({"status": "ok"})


@login_required
def update_quest_notes(request, quest_id):
    """Save a quest's notes text.

    Uses the same POST-only safety pattern as our other quest
    actions. Redirects back to whichever day the quest belongs to.
    """

    if request.method == "POST":
        quest = get_object_or_404(Quest, id=quest_id, user=request.user)

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


@login_required
def update_day_notes(request, year, month, day):
    """Save the general notes for a specific day.

    Unlike quest notes, this always operates on a specific date
    passed in via the URL — matching how the schedule page itself
    can show any day, not just today. Scoped to request.user.
    """

    if request.method == "POST":
        viewed_date = timezone.datetime(
            year=year, month=month, day=day
        ).date()

        day_schedule, _ = DaySchedule.objects.get_or_create(
            date=viewed_date, user=request.user
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


@login_required
def set_start_time(request, year, month, day):
    """Set a day's start time to one of a few quick preset values.

    Used by quick-select buttons as a faster alternative to typing.
    Scoped to request.user.
    """

    if request.method == "POST":
        viewed_date = timezone.datetime(
            year=year, month=month, day=day
        ).date()

        new_time_str = request.POST.get("start_time")

        if new_time_str:
            new_time = datetime.strptime(
                new_time_str, "%H:%M"
            ).time()

            day_schedule, _ = DaySchedule.objects.get_or_create(
                date=viewed_date, user=request.user
            )
            day_schedule.start_time = new_time
            day_schedule.save()

        return redirect(
            "today_schedule_dated",
            year=viewed_date.year,
            month=viewed_date.month,
            day=viewed_date.day,
        )

    return redirect("today_schedule")


@login_required
def start_my_day(request):
    """Commit to starting today, capturing the real current time.

    This only ever applies to the actual current day. Once set,
    day_started and start_time are treated as locked; this view is
    the only place that ever sets them. Scoped to request.user.
    """

    if request.method == "POST":
        today = timezone.localdate()

        day_schedule, _ = DaySchedule.objects.get_or_create(
            date=today, user=request.user
        )

        # Only act if the day hasn't already been started
        if not day_schedule.day_started:
            day_schedule.start_time = timezone.localtime().time()
            day_schedule.day_started = True
            day_schedule.save()

    return redirect("today_schedule")


@login_required
def unlink_quest_from_goal(request, quest_id):
    """Remove a quest's link to its goal, without deleting the quest.

    The quest stays exactly where it is on its scheduled day — it
    just becomes a plain, goal-less quest afterward.
    """

    if request.method == "POST":
        quest = get_object_or_404(Quest, id=quest_id, user=request.user)

        # Remember which goal it was linked to, to redirect back
        goal_id = quest.goal_id

        quest.goal = None
        quest.save()

        if goal_id:
            return redirect("goal_detail", goal_id=goal_id)

    return redirect("today_schedule")