from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from accounts.models import Profile


class Command(BaseCommand):
    """
    Create a Profile for any existing User that doesn't have one.

    Needed because our post_save signal only creates a Profile at
    the moment a User is created - any User made before that signal
    existed (or created some other way that skips it) is missing
    one. Run with: python manage.py backfill_profiles
    """

    help = "Create a Profile for any User missing one"

    def handle(self, *args, **kwargs):
        # Loop through every existing user, and check whether a
        # Profile for them already exists. hasattr() safely checks
        # for an attribute without crashing if it's missing.
        created_count = 0

        for user in User.objects.all():
            if not hasattr(user, "profile"):
                Profile.objects.create(user=user)
                created_count += 1
                self.stdout.write(f"CReated profile for {user.username}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done - created {created_count} missing profile(s)."
            )
        )