from __future__ import annotations

from logging import getLogger
from typing import Dict, Iterable, Tuple

from django import forms
from django.conf import settings

from ..submissions.models import Submission
from .models import Assignment, Folder, MossResult

logger = getLogger(__name__)


class AssignmentForm(forms.ModelForm):
    QUIZ_ACTIONS = (("-1", "No"), ("0", "Log only"), ("1", "Color Change"), ("2", "Lock"))

    due = forms.DateTimeInput()
    is_quiz = forms.ChoiceField(choices=QUIZ_ACTIONS)

    def __init__(self, course, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["folder"].queryset = Folder.objects.filter(course=course)

        # Prevent changing the language of an assignment after it has been created
        instance = getattr(self, "instance", None)
        if instance and instance.pk:
            self.fields["language"].help_text = (
                "Changing this after uploading a grader script is not recommended and will cause "
                "issues."
            )

        # prevent description from getting too big
        self.fields["description"].widget.attrs.update({"id": "description"})

    def get_sections(self) -> Iterable[Dict[str, str | Tuple[str, ...] | bool]]:
        for section in self.Meta.sections:
            if section["name"]:
                # operate on copy so errors on refresh don't happen
                section = section.copy()
                section["fields"] = tuple(self[field] for field in section["fields"])
                yield section

    def get_main_section(self) -> Dict[str, str | Tuple[str, ...]]:
        for section in self.Meta.sections:
            if section["name"] == "":
                section = section.copy()
                section["fields"] = tuple(self[field] for field in section["fields"])
                return section
        logger.error(f"Could not find main section for assignment {self}")
        return {"fields": ()}

    class Meta:
        model = Assignment
        fields = [
            "name",
            "description",
            "autocomplete",
            "markdown",
            "folder",
            "language",
            "filename",
            "venv",
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
            "markdown": "Use markdown?",
            "venv": "Virtual environment",
            "hidden": "Hide assignment from students?",
            "enable_grader_timeout": "Set a timeout for the grader?",
            "grader_timeout": "Grader timeout (seconds):",
            "grader_has_network_access": "Give the grader internet access?",
            "has_network_access": "Give submissions internet access?",
            "submission_limit_count": "Rate limit count",
            "submission_limit_interval": "Rate limit interval (minutes)",
            "submission_limit_cooldown": "Rate limit cooldown period (minutes)",
            "is_quiz": "Is this a quiz?",
        }
        sections = (
            {
                "name": "",
                "fields": (
                    "name",
                    "description",
                    "markdown",
                    "due",
                    "points_possible",
                    "is_quiz",
                    "hidden",
                ),
            },
            {
                "name": "Environment Setup",
                "description": "",
                "fields": (
                    "folder",
                    "language",
                    "filename",
                    "venv",
                ),
                "collapsed": False,
            },
            {
                "name": "Submissions",
                "description": "",
                "fields": (
                    "autocomplete",
                    "enable_grader_timeout",
                    "grader_timeout",
                    "has_network_access",
                    "grader_has_network_access",
                    "submission_limit_count",
                    "submission_limit_interval",
                    "submission_limit_cooldown",
                ),
                "collapsed": True,
            },
        )
        help_texts = {
            "filename": "Clarify which file students need to upload (including the file "
            "extension). For Java assignments, this also sets the name of the "
            "saved submission file.",
            "markdown": "This allows adding images, code blocks, or hyperlinks to the assignment description.",
            "venv": "If set, Tin will run the student's code in this virtual environment.",
            "grader_has_network_access": 'If unset, this effectively disables "Give submissions '
            'internet access" below. If set, it increases the amount '
            "of time it takes to start up the grader (to about 1.5 "
            "seconds). This is not recommended unless necessary.",
            "submission_limit_count": "",
            "submission_limit_interval": "Tin sets rate limits on submissions. If a student tries "
            "to submit too many submissions in a given interval, "
            "Tin will block further submissions until a cooldown "
            "period has elapsed since the time of the last "
            "submission.",
            "submission_limit_cooldown": 'This sets the length of the "cooldown" period after a '
            "student exceeds the rate limit for submissions.",
            "folder": "If blank, assignment will show on the main classroom page.",
            "is_quiz": "If set, Tin will take the selected action if a student clicks off of the "
            "submission page.",
        }
        widgets = {"description": forms.Textarea(attrs={"cols": 30, "rows": 4})}

    def __str__(self) -> str:
        return f"AssignmentForm(\"{self['name'].value()}\")"


class GraderScriptUploadForm(forms.Form):
    grader_file = forms.FileField(
        label="Upload grader",
        max_length=settings.SUBMISSION_SIZE_LIMIT,
        allow_empty_file=False,
        help_text="Size limit is 1MB.",
    )


class FileUploadForm(forms.Form):
    upload_file = forms.FileField(
        max_length=settings.SUBMISSION_SIZE_LIMIT,
        allow_empty_file=False,
        help_text="Size limit is 1MB.",
    )


class FileSubmissionForm(forms.Form):
    file = forms.FileField(
        label="",
        max_length=settings.SUBMISSION_SIZE_LIMIT,
        allow_empty_file=False,
        help_text="You can also drag files onto this page to submit them. Size limit is 1MB.",
    )


class TextSubmissionForm(forms.ModelForm):
    text = forms.CharField(label="", widget=forms.Textarea(attrs={"cols": 130, "rows": 20}))

    class Meta:
        model = Submission
        fields = []


class MossForm(forms.ModelForm):
    def __init__(self, assignment, period, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["period"].queryset = assignment.course.period_set.all()
        if period:
            self.fields["period"].initial = period
        self.fields["language"].initial = (
            "java" if assignment.filename.endswith(".java") else "python"
        )

    class Meta:
        model = MossResult
        fields = ["period", "language", "base_file", "user_id"]
        help_texts = {
            "period": "Leave blank to run Moss on all students in the course.",
            "base_file": "The assignment's shell code (optional).",
        }


class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = [
            "name",
        ]
        help_texts = {"name": "Note: Folders are ordered alphabetically."}
