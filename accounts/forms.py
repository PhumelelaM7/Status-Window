from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


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