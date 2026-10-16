from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from quests.models import Quest, DaySchedule
from quests.scheduling import compute_streak, compute_highest_streak
from goals.models import Goal

from .forms import SignUpForm, DisplayNameForm


def signup(request):
    """Show a signup form, and log the user in immediately on success."""

    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            # .save() creates the actual User account. This also
            # triggers our post_save signal, which creates a Profile.
            user = form.save()

            # Log the new user in right away, rather than making
            # them log in again immediately after signing up.
            login(request, user)

            return redirect("today_schedule")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile(request):
    """Show this user's stats and let them change their display name.

    POST saves only display_name on the existing Profile, then
    redirects so a refresh does not resubmit the form. Every
    queryset is filtered by request.user.
    """

    # OneToOne from User; created automatically on signup.
    user_profile = request.user.profile

    if request.method == "POST":
        form = DisplayNameForm(request.POST, instance=user_profile)
        if form.is_valid():
            # instance= writes onto the existing row, not a new Profile.
            form.save()
            return redirect("profile")
    else:
        form = DisplayNameForm(instance=user_profile)

    # Completed quests and goals, this user only.
    quests_completed = Quest.objects.filter(
        user=request.user, is_completed=True
    ).count()
    goals_completed = Goal.objects.filter(
        user=request.user, is_completed=True
    ).count()

    # Same cleared-date set the day page uses, so the numbers match.
    cleared_dates = set(
        DaySchedule.objects.filter(
            user=request.user, is_cleared=True
        ).values_list("date", flat=True)
    )
    # Current streak ends today. Highest is the longest run ever.
    streak = compute_streak(cleared_dates, timezone.localdate())
    highest_streak = compute_highest_streak(cleared_dates)

    context = {
        "profile": user_profile,
        "form": form,
        "quests_completed": quests_completed,
        "goals_completed": goals_completed,
        "streak": streak,
        "highest_streak": highest_streak,
        "date_joined": request.user.date_joined,
    }
    return render(request, "accounts/profile.html", context)