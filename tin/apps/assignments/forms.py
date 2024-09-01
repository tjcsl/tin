from __future__ import annotations

from collections.abc import Iterable
from logging import getLogger
from typing import Literal, Self

from django import forms
from django.conf import settings
from django.core.validators import ValidationError
from typing_extensions import TypedDict

from ..submissions.models import Submission
from .models import Assignment, Course, FileAction, Folder, MossResult

logger = getLogger(__name__)


class AssignmentForm(forms.ModelForm):
    due = forms.DateTimeInput()

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

    def get_sections(self) -> Iterable[dict[str, str | tuple[str, ...] | bool]]:
        """This is used in templates to find which fields should be in a dropdown div."""
        for section in self.Meta.sections:
            if section["name"]:
                # operate on copy so errors on refresh don't happen
                new_section = section.copy()
                new_section["fields"] = tuple(self[field] for field in new_section["fields"])
                yield new_section

    def get_main_section(self) -> dict[str, str | tuple[str, ...]]:
        """This is the section that is NOT in a dropdown"""
        for section in self.Meta.sections:
            if section["name"] == "":
                new_section = section.copy()
                new_section["fields"] = tuple(self[field] for field in new_section["fields"])
                return new_section
        logger.error(f"Could not find main section for assignment {self}")
        return {"fields": ()}

    class Meta:
        model = Assignment
        fields = [
            "name",
            "description",
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
            "is_quiz",
            "quiz_action",
            "quiz_autocomplete_enabled",
            "quiz_description",
            "quiz_description_markdown",
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
            "quiz_autocomplete_enabled": "Enable code autocompletion?",
            "quiz_description_markdown": "Use markdown?",
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
                "name": "Quiz Options",
                "description": "",
                "fields": (
                    "is_quiz",
                    "quiz_action",
                    "quiz_autocomplete_enabled",
                    "quiz_description",
                    "quiz_description_markdown",
                ),
                "collapsed": False,
            },
            {
                "name": "Other Settings",
                "description": "",
                "fields": (
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
            "is_quiz": "This forces students to submit through a page that monitors their actions. The below options "
            "have no effect if this is unset.",
            "quiz_action": "Tin will take the selected action if a student clicks off of the "
            "quiz page.",
            "quiz_autocomplete_enabled": "This gives students basic code completion in the quiz editor, including "
            "variable names, built-in functions, and keywords. It's recommended for quizzes that focus on code logic "
            "and not syntax.",
            "quiz_description": "Unlike the assignment description (left) which shows up on the assignment page, the "
            "quiz description only appears once the student has started the quiz. This is useful for quiz "
            "instructions that need to be hidden until the student enters the monitored quiz environment.",
            "quiz_description_markdown": "This allows adding images, code blocks, or hyperlinks to the quiz "
            "description.",
        }
        widgets = {
            "description": forms.Textarea(attrs={"cols": 30, "rows": 8}),
            "quiz_description": forms.Textarea(attrs={"cols": 30, "rows": 6}),
        }

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


class FileActionArgs(TypedDict):
    name: str
    command: str
    match_type: Literal["", "S", "E", "C"]
    match_value: str
    case_sensitive_match: bool


class FileActionForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.fields["courses"] = forms.ModelMultipleChoiceField(
            queryset=Course.objects.filter_editable(user),
            required=True,
        )

    class Meta:
        model = FileAction
        fields = [
            "name",
            "command",
            "courses",
            "match_type",
            "match_value",
            "case_sensitive_match",
        ]
        help_texts = {
            "command": "You can use $FILE to reference the file that matches the below criteria."
        }

    JAVAC: FileActionArgs = {
        "name": "Compile Java Files",
        "command": "javac $FILE",
        "match_type": "E",
        "match_value": "java",
        "case_sensitive_match": True,
    }

    RANDOM_TEXT_FILES: FileActionArgs = {
        "name": "Generate text files with random content",
        "command": "base64 /dev/urandom | head -c 500 > file.txt",
        "match_type": "",
        "match_value": "",
        "case_sensitive_match": False,
    }

    # TODO: add others

    TEMPLATES: dict[str, FileActionArgs] = {
        "javac": JAVAC,
        "random_text_files": RANDOM_TEXT_FILES,
    }

    @classmethod
    def from_template(cls, template: str, user) -> Self:
        """Takes in a template name and returns a :class:`.FileActionForm`.

        Args:
            template: The name of the template to use.
            user: ``request.user``, which is needed to filter the courses.
        """
        if config := cls.TEMPLATES.get(template):
            return cls(user, data=config)
        raise ValueError(f"Invalid template: {template!r}")


class ChooseFileActionForm(forms.Form):
    def __init__(self, *args, user, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        choices = [
            (k, v["name"])  # type: ignore[arg-type]
            for k, v in FileActionForm.TEMPLATES.items()
        ] + [("custom", "Custom")]

        self.fields["actions"] = forms.ChoiceField(
            choices=choices,
            required=True,
            widget=forms.widgets.RadioSelect(),
            label="File Action Template",
        )

        self.fields["courses"] = forms.ModelMultipleChoiceField(
            queryset=Course.objects.filter_editable(user),
            required=False,
            help_text="Which courses to add the file action too. Only required if using a template.",
        )

    def clean(self):
        super().clean()
        if self.cleaned_data.get("actions") != "custom" and not self.cleaned_data.get("courses"):
            error = ValidationError("Must select courses if using a template", code="invalid")
            self.add_error("courses", error)
