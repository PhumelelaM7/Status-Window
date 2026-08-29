from django import forms
from .models import Goal


class GoalForm(forms.ModelForm):
    """Form for creating or editing a Goal."""

    class Meta:
        model = Goal

        # Added end_date so the user can set an optional deadline
        # when creating or editing a goal
        fields = [
            "title",
            "why_it_matters",
            "success_definition",
            "term",
            "end_date",
        ]

        widgets = {
            "term": forms.Select(),
            "why_it_matters": forms.Textarea(attrs={"rows": 3}),
            "success_definition": forms.Textarea(attrs={"rows": 3}),
            # A proper date picker, same technique as the reschedule
            # form's date input
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }