from django.db import models
from goals.models import Goal
from datetime import time

class Quest(models.Model):
    """A single scheduled task on a given day.

    Quests can exist on their own (a plain daily schedule item) or
    be linked to a Goal, in which case completing quests is how a
    goal actually gets worked on day to day.

    start_time is no longer typed in directly for most quests — it
    gets computed from order + duration, the same way the original
    Kivy version's compute_schedule() worked. It stays on the model
    so we can still store/display the result, but the view will
    recalculate and overwrite it based on order.
    """

    # Short label for the quest, e.g. "Read Python docs, chapter 3"
    title = models.CharField(max_length=200)

    # Optional link back to a Goal. blank=True lets the admin form
    # leave it empty; null=True lets the database store "no goal".
    # on_delete=SET_NULL means if a Goal is deleted, linked quests
    # survive as plain, goal-less quests rather than being deleted.
    goal = models.ForeignKey(
        Goal,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="quests",
    )

    # The calendar date this quest is scheduled for
    scheduled_date = models.DateField()

    # Position within the day's schedule, lowest first. This is
    # what lets quests be reordered, the way the original app's
    # up/down arrows worked.
    order = models.PositiveIntegerField(default=0)

    # Whether this quest currently counts toward today's schedule.
    # A disabled quest is skipped when computing start/end times,
    # but stays in the database rather than being deleted.
    is_enabled = models.BooleanField(default=True)

    # What time the schedule starts for this day
    start_time = models.TimeField(default=time(9, 30))

    # When set, this quest's start time is "pinned" to this exact
    # clock time rather than following the normal cascade from the
    # previous quest. Used by reschedule: moving a quest to a new
    # time should make it actually start there, not just fall
    # wherever the running total happens to land.
    anchor_time = models.TimeField(blank=True, null=True)

    # How long the quest is expected to take, in minutes
    duration_minutes = models.PositiveIntegerField(default=30)

    # Whether the quest has been completed
    is_completed = models.BooleanField(default=False)

    # Whether this quest's time passed while still incomplete and
    # the user chose not to reschedule it — a permanent, separate
    # state from is_completed. A quest can't be both completed and
    # failed; our own logic (not the database) will enforce that.
    is_failed = models.BooleanField(default=False)

    # Timestamp for when it was actually marked complete (if it was)
    completed_at = models.DateTimeField(blank=True, null=True)

    # Free-text notes the user can attach to this quest
    notes = models.TextField(blank=True)

    class Meta:
        # Default ordering whenever we query Quest without
        # specifying our own .order_by() — keeps the schedule
        # order consistent everywhere we use it
        ordering = ["scheduled_date", "order"]

    def __str__(self):
        # Shown in the Django admin panel and shell for readability
        return f"{self.title} ({self.scheduled_date})"


class DaySchedule(models.Model):
    """Per-day settings: what time the schedule starts, whether the
    day has been marked cleared (streak tracking), and whether
    "reschedule from now" is active (Water ring: flows remaining
    quests forward to the current time when running behind).

    One row per calendar date. Quests reference a date directly
    rather than a DaySchedule, so a DaySchedule only needs to exist
    once someone sets a custom start time or clears the day.
    """

    # One row per calendar date — no two DaySchedules can share a date
    date = models.DateField(unique=True)

    # What time the schedule starts for this day
    start_time = models.TimeField(default=time(9, 30))

    # Whether this day has been marked "cleared" (all quests done,
    # or the user chose to close it out) — used for streak counting
    is_cleared = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.date} (starts {self.start_time})"