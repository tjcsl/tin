from django import forms
from django.conf import settings

from ..submissions.models import Submission
from .models import Assignment, Folder


class AssignmentForm(forms.ModelForm):
    due = forms.DateTimeInput()

    def __init__(self, course, *args, **kwargs):
        super(AssignmentForm, self).__init__(*args, **kwargs)
        self.fields["folder"].queryset = Folder.objects.filter(course=course)

    class Meta:
        model = Assignment
        fields = [
            "name",
            "description",
            "folder",
            "points_possible",
            "due",
            "hidden",
            "enable_grader_timeout",
            "grader_timeout",
            "grader_has_network_access",
            "has_network_access",
            "submission_limit_count",
            "submission_limit_interval",
            "submission_limit_cooldown",
        ]
        labels = {
            "hidden": "Hide assignment from students?",
            "enable_grader_timeout": "Set a timeout for the grader?",
            "grader_timeout": "Grader timeout (seconds):",
            "grader_has_network_access": "Give the grader internet access?",
            "has_network_access": "Give submissions internet access?",
            "submission_limit_count": "Rate limit count",
            "submission_limit_interval": "Rate limit interval (minutes)",
            "submission_limit_cooldown": "Rate limit cooldown period (minutes)",
        }
        help_texts = {
            "grader_has_network_access": 'If unset, this effectively disables "Give submissions'
            ' internet access" below. If set, it increases the amount of time it takes to start up'
            " the grader (to about 1.5 seconds). This is not recommended unless necessary.",
            "submission_limit_count": "",
            "submission_limit_interval": "Tin sets rate limits on submissions. If a student tries "
            "to submit too many submissions in a given interval, Tin will block further "
            "submissions until a cooldown period has elapsed since the time of the last "
            "submission.",
            "submission_limit_cooldown": 'This sets the length of the "cooldown" period after a '
            "student exceeds the rate limit for submissions.",
            "folder": "If blank, assignment will show on the main classroom page.",
        }
        widgets = {"description": forms.Textarea(attrs={"cols": 40, "rows": 12})}


class GraderFileSubmissionForm(forms.Form):
    grader_file = forms.FileField(
        max_length=settings.SUBMISSION_SIZE_LIMIT,
        allow_empty_file=False,
    )


class SuperuserFileSubmissionForm(forms.Form):
    assignment = forms.ModelChoiceField(queryset=Assignment.objects.all())
    upload_file = forms.FileField(
        max_length=settings.SUBMISSION_SIZE_LIMIT,
        allow_empty_file=False,
    )


class FileSubmissionForm(forms.Form):
    file = forms.FileField(
        max_length=settings.SUBMISSION_SIZE_LIMIT,
        allow_empty_file=False,
        help_text="You can also drag files onto this page to submit them.",
    )


class TextSubmissionForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={"cols": 80, "rows": 20}))

    class Meta:
        model = Submission
        fields = []


class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = [
            "name",
        ]
