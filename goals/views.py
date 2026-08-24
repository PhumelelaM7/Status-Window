from django.shortcuts import render, get_object_or_404, redirect
from .models import Goal
from .forms import GoalForm


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
    # crashing if the id doesn't exist — safer than Goal.objects.get()
    goal = get_object_or_404(Goal, id=goal_id)

    # goal.quests uses the related_name="quests" we set on the
    # Quest model's ForeignKey — this follows the link backwards,
    # from a Goal to every Quest that points at it
    quests = goal.quests.all().order_by("scheduled_date", "start_time")

    context = {
        "goal": goal,
        "quests": quests,
    }

    return render(request, "goals/goal_detail.html", context)


def add_goal(request):
    """
    Show a form to add a new goal, and save it on submission.
    """

    # A GET request means the page was just visited (show blank
    # form). A POST request means the form was submitted.
    if request.method == "POST":
        form = GoalForm(request.POST)

        if form.is_valid():
            # .save() writes a new Goal row to the database
            form.save()

            # Redirect back to the goals list, following the same
            # Post/Redirect/Get pattern used everywhere else in
            # this project - avoids resubmitting the form on refresh
            return redirect("goal_list")
    else:
        # No data submitted yet - show an empty form
        form = GoalForm()

    return render(request, "goals/add_goal.html", {"form": form})
