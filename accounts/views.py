from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import SignUpForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from quests.models import Quest, DaySchedule
from goals.models import Goal


def signup(request):
    """Show a signup form, and log the user in immediately on success."""

    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            # .save() creates the actual User account. This also
            # triggers our post_save signal from earlier, which
            # automatically creates a matching Profile.
            user = form.save()

            # Log the new user in right away, rather than making
            # # them log in again immediately after signup up
            login(request, user)

            return redirect("today_schedule")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile(request):
    """Show the current user's profile stats and allow editing display name."""

    profile = request.user.profile

    # Stats
    quests_completed = Quest.objects.filter(
        user=request.user, is_completed=True
    ).count()

    goals_completed = Goal.objects.filter(
        user=request.user, is_completed=True
    ).count()

    # Highest streak (simple version: count consecutive cleared days from today backwards)
    # For now we just show total cleared days as a starting point
    days_cleared = DaySchedule.objects.filter(
        user=request.user, is_cleared=True
    ).count()

    context = {
        "profile": profile,
        "quests_completed": quests_completed,
        "goals_completed": goals_completed,
        "days_cleared": days_cleared,
        "date_joined": request.user.date_joined,
    }

    return render(request, "accounts/profile.html", context)