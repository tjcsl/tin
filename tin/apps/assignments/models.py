from __future__ import annotations

import datetime
import logging
import os
import subprocess
from typing import Literal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from ...sandboxing import get_action_sandbox_args, get_assignment_sandbox_args
from ..courses.models import Course, Period
from ..submissions.models import Submission
from ..venvs.models import Venv

logger = logging.getLogger(__name__)


class Folder(models.Model):
    """A folder for assignments.

    Each course can have multiple folders, and each
    assignment can be in a folder.
    """

    name = models.CharField(max_length=50)

    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="folders")

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("assignments:show_folder", args=[self.course.id, self.id])


class AssignmentQuerySet(models.query.QuerySet):
    def filter_permissions(self, user, *perms: Literal["-", "r", "w"]):
        """Filters based off of the permissions of the user and the course.

        An admin can always see everything. A teacher can only see courses they
        are the teachers for. Otherwise it filters it based off the course being archived
        and/or the permission of the course after archiving.

        Args:
            user: The user executing the query (``request.user``)
            *perms: Every permission listed is or-ed together.
                Each value can be - (hidden), r (read-only), or w (read-write)
        """
        if user.is_superuser:
            return self.all()
        else:
            perm_q = Q(course__archived=False)
            for perm in perms:
                perm_q |= Q(course__permission=perm)
            q = Q(course__teacher=user) | (Q(course__students=user, hidden=False) & perm_q)

            return self.filter(q).distinct()

    def filter_visible(self, user):
        r"""Filters assignments that are visible to a user

        Alias for calling :meth:`filter_permissions` with the permissions
        "r" and "w"
        """
        return self.filter_permissions(user, "r", "w")

    def filter_submittable(self, user):
        """Filters by assignments that can be submitted.

        .. warning::

            Do NOT use this if :attr:`~Assignment.is_quiz` is ``True``.
            In that case, the check should be done manually.
        """
        return self.filter_permissions(user, "w")

    def filter_editable(self, user):
        """Filters assignments if they're editable by the user"""
        if user.is_superuser:
            return self.all()
        else:
            return self.filter(course__teacher=user).distinct()


def upload_grader_file_path(assignment, _):  # pylint: disable=unused-argument
    """Get the location of the grader file for an assignment"""
    assert assignment.id is not None
    if assignment.language == "P":
        return f"assignment-{assignment.id}/grader.py"
    else:
        return f"assignment-{assignment.id}/Grader.java"


class Assignment(models.Model):
    """An assignment (or quiz) for a student.

    If :attr:`~.Assignment.is_quiz` is ``True``, this
    model doubles as a quiz.

    The manager for this model is :class:`.AssignmentQuerySet`.
    """

    name = models.CharField(max_length=50)
    folder = models.ForeignKey(
        Folder,
        on_delete=models.SET_NULL,
        default=None,
        null=True,
        blank=True,
        related_name="assignments",
    )
    description = models.CharField(max_length=4096)
    markdown = models.BooleanField(default=False)

    LANGUAGES = (
        ("P", "Python 3"),
        ("J", "Java"),
    )
    language = models.CharField(max_length=1, choices=LANGUAGES, default="P")

    filename = models.CharField(max_length=50, default="main.py")

    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="assignments"
    )

    venv = models.ForeignKey(
        Venv,
        on_delete=models.SET_NULL,
        default=None,
        null=True,
        blank=True,
        related_name="assignments",
    )

    points_possible = models.DecimalField(
        max_digits=6, decimal_places=3, validators=[MinValueValidator(1)]
    )

    assigned = models.DateTimeField(auto_now_add=True)
    due = models.DateTimeField()
    hidden = models.BooleanField(default=False)

    grader_file = models.FileField(upload_to=upload_grader_file_path, null=True)
    enable_grader_timeout = models.BooleanField(default=True)
    grader_timeout = models.IntegerField(default=300, validators=[MinValueValidator(10)])

    grader_has_network_access = models.BooleanField(default=False)

    has_network_access = models.BooleanField(default=False)

    # WARNING: this is the rate limit
    submission_limit_count = models.PositiveIntegerField(
        default=90,
        validators=[MinValueValidator(10)],
    )
    submission_limit_interval = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(10)],
    )
    submission_limit_cooldown = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(10)],
    )

    last_action_output = models.CharField(max_length=16 * 1024, default="", null=False, blank=True)

    is_quiz = models.BooleanField(default=False)
    QUIZ_ACTIONS = (("0", "Log only"), ("1", "Color Change"), ("2", "Lock"))
    quiz_action = models.CharField(max_length=1, choices=QUIZ_ACTIONS, default="2")
    quiz_autocomplete_enabled = models.BooleanField(default=False)
    quiz_description = models.CharField(max_length=4096, default="", null=False, blank=True)
    quiz_description_markdown = models.BooleanField(default=False)

    objects = AssignmentQuerySet.as_manager()

    submission_caps: models.QuerySet[SubmissionCap]

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("assignments:show", args=(self.id,))

    def within_submission_limit(self, student) -> bool:
        """Check if a student is within the submission limit for an assignment."""
        # teachers should have infinite submissions
        if not student.is_student or self.is_quiz or not self.submission_caps.exists():
            return True

        # note that this doesn't care about killed/incomplete submissions
        submission_count = self.submissions.filter(student=student).count()

        cap = self.find_submission_cap(student)
        return submission_count < cap

    def find_submission_cap(self, student) -> float:
        """Given a student, find the submission cap.

        This takes into account student overrides, and due dates.
        """
        if student.is_superuser or student.is_teacher:
            return float("inf")
        if timezone.localtime() > self.due:
            return self.submission_cap_after_due(student)
        return self.before_submission_cap(student)

    def find_student_override(self, student) -> SubmissionCap | None:
        """Find an :class:`.SubmissionCap` for a student.

        Returns ``None`` if no override exists.
        """
        return self.submission_caps.filter(student=student).first()

    def before_submission_cap(self, student) -> float:
        """Get the submission cap for an assignment before the due date.

        Returns ``float("inf")`` if no cap is found.
        """
        student_cap = self.find_student_override(student)
        if student_cap is not None and student_cap.submission_cap is not None:
            return student_cap.submission_cap
        cap = self.submission_caps.filter(student__isnull=True).first()
        if cap is not None and cap.submission_cap is not None:
            return cap.submission_cap
        return float("inf")

    def submission_cap_after_due(self, student) -> float:
        """Get the submission cap after the due date.

        Returns ``float("inf")`` if no cap is found.
        """
        student_cap = self.find_student_override(student)
        if student_cap is not None and student_cap.submission_cap_after_due is not None:
            return student_cap.submission_cap_after_due
        cap = self.submission_caps.filter(student__isnull=True).first()
        if cap is not None and cap.submission_cap_after_due is not None:
            return cap.submission_cap_after_due
        # fall back to the submission cap before the due date
        return self.before_submission_cap(student)

    def make_assignment_dir(self) -> None:
        """Creates the directory where the assignment grader scripts go."""
        assignment_path = os.path.join(settings.MEDIA_ROOT, f"assignment-{self.id}")
        os.makedirs(assignment_path, exist_ok=True)

    def save_grader_file(self, grader_text: str) -> None:
        """Save the grader file to the correct location.

        .. warning::

            Writing to files in directories not controlled by us without some
            form of sandboxing is a security risk. Most notably, users can use symbolic
            links to trick you into writing to another file, outside the directory.
            they control.
            This solution is very hacky, but we don't have another good way of
            doing this.
        """
        fname = upload_grader_file_path(self, "")

        self.grader_file.name = fname
        self.save()

        fpath = os.path.join(settings.MEDIA_ROOT, self.grader_file.name)

        os.makedirs(os.path.dirname(fpath), exist_ok=True)

        args = get_assignment_sandbox_args(
            ["sh", "-c", 'cat >"$1"', "sh", fpath],
            network_access=False,
            whitelist=[os.path.dirname(fpath)],
        )

        try:
            subprocess.run(
                args,
                input=grader_text,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                text=True,
                check=True,
            )
        except FileNotFoundError as e:
            logger.error("Cannot run processes: %s", e)
            raise FileNotFoundError from e

    def list_files(self) -> list[tuple[int, str, str, int, datetime.datetime]]:
        """List all files in the assignments directory

        Returns:
            - The index of the assignment
            - The name of the assignment submission
            - The full path to the assignment submission
            - The size of the submission
            - The time at which it was submitted
        """
        self.make_assignment_dir()

        assignment_path = os.path.join(settings.MEDIA_ROOT, f"assignment-{self.id}")

        files = []
        grader_file = upload_grader_file_path(self, "")
        grader_log_file = self.grader_log_filename

        for i, item in enumerate(os.scandir(assignment_path)):
            if item.is_file():
                stat = item.stat(follow_symlinks=False)
                item_details = (
                    i,
                    item.name,
                    item.path,
                    stat.st_size,
                    datetime.datetime.fromtimestamp(stat.st_mtime),
                )
                if not grader_file.endswith(item.name) and not grader_log_file.endswith(item.name):
                    files.append(item_details)

        return files

    def save_file(self, file_text: str, file_name: str) -> None:
        """Save some text as a file"""
        self.make_assignment_dir()

        fpath = os.path.join(settings.MEDIA_ROOT, f"assignment-{self.id}", file_name)

        os.makedirs(os.path.dirname(fpath), exist_ok=True)

        args = get_assignment_sandbox_args(
            ["sh", "-c", 'cat >"$1"', "sh", fpath],
            network_access=False,
            whitelist=[os.path.dirname(fpath)],
        )

        try:
            subprocess.run(
                args,
                input=file_text,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                text=True,
                check=True,
            )
        except FileNotFoundError as e:
            logger.error("Cannot run processes: %s", e)
            raise FileNotFoundError from e

    def get_file(self, file_id: int) -> tuple[str, str]:
        self.make_assignment_dir()

        for i, item in enumerate(
            os.scandir(os.path.join(settings.MEDIA_ROOT, f"assignment-{self.id}"))
        ):
            if i == file_id and os.path.exists(item.path) and item.is_file():
                return item.name, item.path
        return "", ""

    def delete_file(self, file_id: int) -> None:
        """Delete a file by id"""
        self.make_assignment_dir()

        for i, item in enumerate(
            os.scandir(os.path.join(settings.MEDIA_ROOT, f"assignment-{self.id}"))
        ):
            if i == file_id and os.path.exists(item.path) and item.is_file():
                os.remove(item.path)
                return

    def check_rate_limit(self, student) -> None:
        """Check if a student is submitting too quickly"""
        now = timezone.localtime()

        if (
            Submission.objects.filter(
                date_submitted__gte=now
                - datetime.timedelta(minutes=self.submission_limit_interval),
                student=student,
            ).count()
            > self.submission_limit_count
        ):
            with transaction.atomic():
                current_cooldown = CooldownPeriod.objects.filter(
                    assignment=self, student=student
                ).first()
                if current_cooldown:
                    current_cooldown.delete()
                CooldownPeriod.objects.create(assignment=self, student=student)

    @property
    def venv_fully_created(self):
        return self.venv and self.venv.fully_created

    @property
    def grader_log_filename(self) -> str:
        return f"{upload_grader_file_path(self, '').rsplit('.', 1)[0]}.log"

    def quiz_open_for_student(self, student):
        """Check if a quiz is open for a specific student"""
        is_teacher = self.course.teacher.filter(id=student.id).exists()
        if is_teacher or student.is_superuser:
            return True
        return not (self.quiz_ended_for_student(student) or self.quiz_locked_for_student(student))

    def quiz_ended_for_student(self, student) -> bool:
        """Check if the quiz has ended for a student"""
        return self.log_messages.filter(student=student, content="Ended quiz").exists()

    def quiz_locked_for_student(self, student) -> bool:
        """Check if the quiz has been locked (e.g. due to leaving the tab)"""
        return self.quiz_issues_for_student(student) and self.quiz_action == "2"

    def quiz_issues_for_student(self, student) -> bool:
        """Check if the student has exceeded the maximum amount of issues they can have with a quiz."""
        return (
            sum(lm.severity for lm in self.log_messages.filter(student=student))
            >= settings.QUIZ_ISSUE_THRESHOLD
        )


class SubmissionCap(models.Model):
    """Submission cap information"""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submission_caps",
    )

    submission_cap = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
    )
    submission_cap_after_due = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            # TODO: In django 5.0+ add nulls_distinct=False
            models.UniqueConstraint(fields=["student", "assignment"], name="unique_type"),
            models.CheckConstraint(
                check=Q(submission_cap__isnull=False) | Q(submission_cap_after_due__isnull=False),
                violation_error_message="Either the submission cap before or after the due date has to be set",
                name="has_submission_cap",
            ),
        ]

    def __str__(self) -> str:
        return f"{type(self).__name__}(submission_cap={self.submission_cap})"


class CooldownPeriod(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="cooldown_periods",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cooldown_periods",
    )

    start_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="unique_assignment_student",
                fields=["assignment", "student"],
            ),
        ]

    def __str__(self):
        return f"{self.student} cooldown on {self.assignment}"

    def __repr__(self):
        return f"{self.student} cooldown on {self.assignment}"

    @classmethod
    def exists(cls, assignment: Assignment, student) -> bool:
        try:
            obj = cls.objects.get(assignment=assignment, student=student)
        except cls.DoesNotExist:
            return False
        else:
            if obj.get_time_to_end() < datetime.timedelta():
                # Ended already
                return False
            else:
                return True

    def get_time_to_end(self) -> datetime.timedelta:
        return (
            self.start_time
            + datetime.timedelta(minutes=self.assignment.submission_limit_cooldown)
            - timezone.localtime()
        )


class Quiz(models.Model):
    """A Quiz Model

    .. warning::

        This model is deprecated and will be removed in the future.
        It is kept for backwards compatibility with existing data.
        All fields and methods have been migrated to the :class:`.Assignment` model

    """

    QUIZ_ACTIONS = (("0", "Log only"), ("1", "Color Change"), ("2", "Lock"))

    assignment = models.OneToOneField(
        Assignment,
        on_delete=models.CASCADE,
    )
    action = models.CharField(max_length=1, choices=QUIZ_ACTIONS)

    class Meta:
        verbose_name_plural = "quizzes"

    def __str__(self):
        return f"Quiz for {self.assignment}"

    def __repr__(self):
        return f"Quiz for {self.assignment}"

    def get_absolute_url(self):
        return reverse("assignments:show", args=(self.assignment.id,))

    def issues_for_student(self, student):
        return (
            sum(lm.severity for lm in self.assignment.log_messages.filter(student=student))
            >= settings.QUIZ_ISSUE_THRESHOLD
        )

    def open_for_student(self, student):
        is_teacher = student in self.assignment.course.teacher.all()
        if is_teacher or student.is_superuser:
            return True
        return not (self.locked_for_student(student) or self.ended_for_student(student))

    def locked_for_student(self, student):
        return self.issues_for_student(student) and self.action == "2"

    def ended_for_student(self, student):
        return self.assignment.log_messages.filter(student=student, content="Ended quiz").exists()


class QuizLogMessage(models.Model):
    """A log message for an :class:`Assignment` (with :attr:`~.Assignment.is_quiz` set to ``True``)"""

    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="log_messages"
    )
    student = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="log_messages"
    )

    date = models.DateTimeField(auto_now_add=True)
    content = models.CharField(max_length=100)
    severity = models.IntegerField()

    def __str__(self):
        return f"{self.content} for {self.assignment} by {self.student}"

    def __repr__(self):
        return f"{self.content} for {self.assignment} by {self.student}"

    def get_absolute_url(self):
        return reverse("assignments:student_submission", args=(self.assignment.id, self.student.id))


def moss_base_file_path(obj, _):  # pylint: disable=unused-argument
    assert obj.assignment.id is not None
    return f"assignment-{obj.assignment.id}/moss-{obj.id}/base.{obj.extension}"


class MossResult(models.Model):
    # from http://moss.stanford.edu/general/scripts.html
    LANGUAGES = (
        ("c", "C"),
        ("cc", "C++"),
        ("java", "Java"),
        ("ml", "ML"),
        ("pascal", "Pascal"),
        ("ada", "Ada"),
        ("lisp", "Lisp"),
        ("scheme", "Scheme"),
        ("haskell", "Haskell"),
        ("fortran", "Fortran"),
        ("ascii", "ASCII"),
        ("vhdl", "VHDL"),
        ("verilog", "Verilog"),
        ("perl", "Perl"),
        ("matlab", "Matlab"),
        ("python", "Python"),
        ("mips", "MIPS"),
        ("prolog", "Prolog"),
        ("spice", "Spice"),
        ("vb", "Visual Basic"),
        ("csharp", "C#"),
        ("modula2", "Modula-2"),
        ("a8086", "a8086 Assembly"),
        ("javascript", "JavaScript"),
        ("plsql", "PL/SQL"),
    )

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="moss_results",
    )
    period = models.ForeignKey(
        Period,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moss_results",
    )

    language = models.CharField(max_length=10, choices=LANGUAGES, default="python")
    base_file = models.FileField(upload_to=moss_base_file_path, null=True, blank=True)
    user_id = models.CharField(max_length=20)

    date = models.DateTimeField(auto_now_add=True)
    url = models.URLField(max_length=200, null=True, blank=True)
    status = models.CharField(max_length=1024, default="", null=False, blank=True)

    def __str__(self):
        return f"Moss result for {self.assignment}"

    def __repr__(self):
        return f"Moss result for {self.assignment}"

    @property
    def extension(self):
        return "java" if self.language == "java" else "py"

    @property
    def download_folder(self):
        return os.path.join(settings.MEDIA_ROOT, "moss-runs", f"moss-{self.id}")


def run_action(command: list[str]) -> str:
    """Runs a command.

    If the command cannot find a file, raises an exception.
    Otherwise, returns the stdout of the command.
    """
    try:
        res = subprocess.run(
            command,
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            text=True,
        )
    except FileNotFoundError as e:
        logger.error("File not found: %s", e)
        raise FileNotFoundError from e
    return res.stdout


class FileAction(models.Model):
    """Runs a user uploaded script on files uploaded to an assignment."""

    MATCH_TYPES = (("S", "Start with"), ("E", "End with"), ("C", "Contain"))

    name = models.CharField(max_length=50)

    courses = models.ManyToManyField(Course, related_name="file_actions")
    command = models.CharField(max_length=1024)

    match_type = models.CharField(max_length=1, choices=MATCH_TYPES, null=True, blank=True)
    match_value = models.CharField(max_length=100, null=True, blank=True)
    case_sensitive_match = models.BooleanField(default=False)

    is_sandboxed = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def run(self, assignment: Assignment):
        """Runs the command on the input assignment"""
        command = self.command.split(" ")

        if (
            ("$FILE" in self.command or "$FILES" in self.command)
            and self.match_type
            and self.match_value
        ):
            filepaths = []

            for file in assignment.list_files():
                if self.case_sensitive_match:
                    filename = file[1]
                    match = self.match_value
                else:
                    filename = file[1].lower()
                    match = self.match_value.lower()

                is_match = (
                    (self.match_type == "S" and filename.startswith(match))
                    or (self.match_type == "E" and filename.endswith(match))
                    or (self.match_type == "C" and match in filename)
                )
                if is_match:
                    filepaths.append(f"{file[2]}")

            if "$FILES" in command:
                new_command = []
                for command_part in command:
                    if command_part == "$FILES":
                        new_command.extend(filepaths)
                    else:
                        new_command.append(command_part)
                command = new_command

            # Special case for multi-command actions
            if "$FILE" in command:
                output = self.name
                for filepath in filepaths:
                    new_command = [filepath if part == "$FILE" else part for part in command]
                    output += "\n-----\n" + " ".join(new_command) + "\n-----\n"
                    if self.is_sandboxed:
                        new_command = get_action_sandbox_args(new_command, network_access=False)
                    output += run_action(new_command)

                assignment.last_action_output = output
                assignment.save()
                return

        if self.is_sandboxed:
            command = get_action_sandbox_args(command, network_access=False)

        output = self.name + "\n" + " ".join(command) + "\n-----\n"
        output += run_action(command)

        assignment.last_action_output = output
        assignment.save()
