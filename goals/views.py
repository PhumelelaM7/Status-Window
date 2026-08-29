from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Goal
from .forms import GoalForm
from .deadlines import compute_countdown


def goal_list(request):
    """Show every goal, split loosely by short-term vs long-term."""

    # Pull all goals from the database, most recently created first
    goals = Goal.objects.all().order_by("-created_at")

    context = {
        "goals": goals,
    }

    return render(request, "goals/goal_list.html", context)


def goal_detail(request, goal_id):
    """Show one goal's details plus every quest linked to it."""

    # get_object_or_404 fetches a single Goal by its id, and
    # automatically shows a proper "not found" page instead of
    # crashing if the id doesn't exist
    goal = get_object_or_404(Goal, id=goal_id)

    # goal.quests uses the related_name="quests" set on Quest's
    # ForeignKey — this follows the link backwards, from a Goal to
    # every Quest that points at it
    quests = goal.quests.all().order_by("scheduled_date", "start_time")

    # Compute the Fire-ring countdown, if this goal has a deadline
    countdown = compute_countdown(goal.end_date, timezone.localdate())

    context = {
        "goal": goal,
        "quests": quests,
        "countdown": countdown,
    }

    return render(request, "goals/goal_detail.html", context)


def add_goal(request):
    """Show a form to add a new goal, and save it on submission."""

    if request.method == "POST":
        form = GoalForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("goal_list")
    else:
        form = GoalForm()

    return render(request, "goals/add_goal.html", {"form": form})


def toggle_goal_complete(request, goal_id):
    """Toggle a goal's is_completed flag on or off."""

    if request.method == "POST":
        goal = get_object_or_404(Goal, id=goal_id)

        goal.is_completed = not goal.is_completed
        goal.is_active = not goal.is_completed

        goal.save()

    return redirect("goal_detail", goal_id=goal_id)