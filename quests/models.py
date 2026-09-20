from django.db import models
from goals.models import Goal
from datetime import time
from django.contrib.auth.models import User


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

    # Which user this quest belongs to. Every quest must have an
    # owner, same reasoning as Goal.
    user = models.ForeignKey(User, on_delete=models.CASCADE)

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

    # Computed/stored start time
    start_time = models.TimeField(default=time(9, 30))

    # When set, this quest's start time is "pinned" to this exact
    # clock time rather than following the normal cascade from the
    # previous quest.
    anchor_time = models.TimeField(blank=True, null=True)

    # How long the quest is expected to take, in minutes
    duration_minutes = models.PositiveIntegerField(default=30)

    # Whether the quest has been completed
    is_completed = models.BooleanField(default=False)

    # Whether this quest's time passed while still incomplete and
    # the user chose not to reschedule it
    is_failed = models.BooleanField(default=False)

    # Timestamp for when it was actually marked complete (if it was)
    completed_at = models.DateTimeField(blank=True, null=True)

    # Free-text notes the user can attach to this quest
    notes = models.TextField(blank=True)

    class Meta:
        # Default ordering whenever we query Quest without
        # specifying our own .order_by()
        ordering = ["scheduled_date", "order"]

    def __str__(self):
        return f"{self.title} ({self.scheduled_date})"


class DaySchedule(models.Model):
    """Per-day settings: what time the schedule starts, whether the
    day has been marked cleared (streak tracking), whether the day
    has been started, and general notes for the day.

    One row per user per calendar date.
    """

    # Which user this day's schedule belongs to — each user has
    # their own independent DaySchedule per calendar date
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # The calendar date this schedule is for
    date = models.DateField()

    # What time the schedule starts for this day
    start_time = models.TimeField(default=time(9, 30))

    # Whether the user has committed to starting this day by
    # pressing "Start My Day"
    day_started = models.BooleanField(default=False)

    # Whether this day has been marked "cleared"
    is_cleared = models.BooleanField(default=False)

    # Free-text notes for the day as a whole
    notes = models.TextField(blank=True)

    class Meta:
        # A user can only have one DaySchedule per date, but
        # different users can each have their own for the same date
        unique_together = ("user", "date")

    def __str__(self):
        return f"{self.date} (starts {self.start_time})"