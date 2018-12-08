from django import forms
from .models import Assignment


class AssignmentForm(forms.ModelForm):
    due = forms.DateTimeInput()

    def __init__(self, *args, **kwargs):
        super(AssignmentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Assignment
        fields = ["name", "description", "points_possible", "due"]
