from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import SignUpForm


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
