from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    """
    Extra information attached to a Django User account.

    Linked one-to-one with Django's built-in User model, rather
    than replaing it - this is the standard, safer way to add
    custom fields to user accounts.
    """

    # OneToOneField means each User has exactly one Profile, and
    # each Profile belongs to exactly one User. on_delete=CASCADE
    # means deleting a User also deletes their profile automatically
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # A friendly display name, seperate from the login username -
    # e.g "Susan" instead of a username like "susan_zps"
    display_name = models.CharField(max_length=100, blank=True)

    # Points earned through the gamified quest/goal system. Starts
    # at 0; the actual awarding logic will be built seperately once
    # this model exists.
    points = models.IntegerField(default=0)

    def __str__(self):
        # Shown in the admin panel - falls back to the username if
        # no display name has been set yet
        return self.display_name or self.user.username


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    """
    Automatically create a Profile whenever a new User is saved.

    post_save fires every time a User is saved, whether newly
    created or just updated. The 'created' flag tells us which - 
    we only want to make a new Profile the first time, not every
    time an existing user's info changes.
    """

    if created:
        Profile.objects.create(user=instance)


