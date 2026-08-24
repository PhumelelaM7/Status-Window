from django import forms
from .models import Goal

class GoalForm(forms.ModelForm):
    """
    Form for creating or editing a Goal.

    Built from the goal model itself, so its fields stay in sync
    automatically of the model changes later.
    """

    class Meta:
        # Tell Django which model this form is based on
        model = Goal

        # Every field the user should be able to set when creating
        # a goal. is_active is left off - new goals should always
        # start active; that field gets managed seperately (e.g.
        # when marking a goal complete).
        fields = [
            "title",
            "why_it_matters",
            "success_definition",
            "term",
        ]

        # Customize how the term dropdown and text areas render.
        # forms.Select gives term a proper dropdown widget instead
        # of the default radio buttons ModelForm would pick for a
        # small choices field
        widgets = {
            "term": forms.Select(),
            "why_it_matters": forms.Textarea(attrs={"rows": 3}),
            "success_definition": forms.Textarea(attrs={"rows": 3})
        }