"""Views for the goals app: listing, creating, viewing, completing,
and unlinking quests from goals — all scoped to the logged-in user.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Goal
from .forms import GoalForm
from .deadlines import compute_countdown


@login_required
def goal_list(request):
    """Show the logged-in user's goals, split by short/long-term."""

    # Only this user's goals — never show another account's data
    goals = Goal.objects.filter(user=request.user).order_by(
        "-created_at"
    )

    context = {
        "goals": goals,
    }

    return render(request, "goals/goal_list.html", context)


@login_required
def goal_detail(request, goal_id):
    """Show one goal's details plus every quest linked to it.

    get_object_or_404 with user=request.user ensures a user can
    never view (or guess the URL to) another account's goal.
    """

    goal = get_object_or_404(Goal, id=goal_id, user=request.user)

    quests = goal.quests.all().order_by("scheduled_date", "start_time")

    countdown = compute_countdown(goal.end_date, timezone.localdate())

    context = {
        "goal": goal,
        "quests": quests,
        "countdown": countdown,
    }

    return render(request, "goals/goal_detail.html", context)


@login_required
def add_goal(request):
    """Show a form to add a new goal, and save it on submission."""

    if request.method == "POST":
        form = GoalForm(request.POST)

        if form.is_valid():
            # Don't save yet — commit=False gives us the Goal
            # object so we can assign ownership before writing it
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()

            return redirect("goal_list")
    else:
        form = GoalForm()

    return render(request, "goals/add_goal.html", {"form": form})


@login_required
def toggle_goal_complete(request, goal_id):
    """Toggle a goal's is_completed flag on or off.

    Marking a goal complete also sets is_active to False, since a
    completed goal isn't something still being actively pursued.
    """

    if request.method == "POST":
        goal = get_object_or_404(Goal, id=goal_id, user=request.user)

        goal.is_completed = not goal.is_completed
        goal.is_active = not goal.is_completed

        goal.save()

    return redirect("goal_detail", goal_id=goal_id)