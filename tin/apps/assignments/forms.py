from django import forms

from ..submissions.models import Submission
from .models import Assignment


class AssignmentForm(forms.ModelForm):
    due = forms.DateTimeInput()

    def __init__(self, *args, **kwargs):
        super(AssignmentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Assignment
        fields = [
            "name",
            "description",
            "points_possible",
            "due",
            "enable_grader_timeout",
            "grader_timeout",
            "has_network_access",
        ]
        labels = {
            "enable_grader_timeout": "Set a timeout for the grader?",
            "grader_timeout": "Grader timeout (seconds):",
            "has_network_access": "Give submissions internet access?",
        }
        widgets = {
            "description": forms.Textarea(attrs={"cols": 40, "rows": 12}),
        }


class GraderFileSubmissionForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ["grader_file"]


class FileSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["file"]


class TextSubmissionForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={"cols": 80, "rows": 20}))

    class Meta:
        model = Submission
        fields = []
