from django import forms
from .models import Quest

class QuestForm(forms.ModelForm):
    """Form for creating or editing a Quest.
    
    Built from the Quest model itself, so its fields and basic
    validation (e.g. required fields, valid time format) stay in
    sync automatically if the model changes later.
    """

    class Meta:
        # Tell Django which model this form is based on.
        model = Quest

        # Which fields from Quest should appear on the form.
        # completed_at is left out here - that gets set by our own
        # logic when a quest is marked done, not typed in by hand.
        fields = [
            "title",
            "goal",
            "scheduled_date",
            "start_time",
            "duration_minutes",
            "notes",
        ]
        # Customize the HTML input type for date/time field so
        # browsers show a proper date/time picker instead of
        # plsin text box.
        widgets = {
            "scheduled_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
        }