from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class SignUpForm(UserCreationForm):
    """
    Signup form based on Django's built-in UserCreationForm.

    UserCreationForm already handles username + password + a
    confirm-password field, including validation (matching
    passwords, password strength rules). We add email as an extra
    field on top of what it provides by default.
    """

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class DisplayNameForm(forms.ModelForm):
    """Edit only the friendly name on the current user's Profile.

    Username stays the login name. Display name is what the app
    shows when it is set.
    """

    class Meta:
        from .models import Profile

        model = Profile
        fields = ["display_name"]
        labels = {"display_name": "Display name"}