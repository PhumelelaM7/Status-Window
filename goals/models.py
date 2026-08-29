from django.db import models


class Goal(models.Model):
    """A user-defined goal the app helps track and pursue.

    Rooted in the Earth ring: a goal must state why it matters
    and what success looks like, not just carry a title.
    """

    # Choices for the term field: stored value, human-readable label
    SHORT_TERM = "short"
    LONG_TERM = "long"
    TERM_CHOICES = [
        (SHORT_TERM, "Short-term"),
        (LONG_TERM, "Long-term"),
    ]

    # Short label for the goal, e.g. "Learn Python"
    title = models.CharField(max_length=200)

    # Earth ring: why this goal matters to the user
    why_it_matters = models.TextField()

    # Earth ring: what success looks like, in the user's own words
    success_definition = models.TextField()

    # Whether this is a short-term or long-term goal
    term = models.CharField(
        max_length=5,
        choices=TERM_CHOICES,
        default=SHORT_TERM,
    )

    # Optional deadline the user sets for this goal — a target to
    # hit. Used to power a countdown display (tied to the Fire
    # ring's emphasis on urgency and full presence). Left blank if
    # the user doesn't want to set one.
    end_date = models.DateField(blank=True, null=True)

    # Timestamp for when the goal was first created
    created_at = models.DateTimeField(auto_now_add=True)

        # Whether the goal is still being actively pursued
    is_active = models.BooleanField(default=True)

    # Whether this goal has actually been achieved. Distinct from
    # is_active — a goal can be inactive without being completed
    # (e.g. abandoned), so this tracks genuine success specifically.
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        # Shown in the Django admin panel and shell for readability
        return self.title