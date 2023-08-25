import datetime
import logging
import os
import subprocess
from typing import List, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from ...sandboxing import get_assignment_sandbox_args
from ..submissions.models import Submission
from ..venvs.models import Virtualenv

logger = logging.getLogger(__name__)


class Folder(models.Model):
    name = models.CharField(max_length=50)

    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="folders")

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("assignments:show_folder", args=[self.course.id, self.id])


class AssignmentQuerySet(models.query.QuerySet):
    def filter_visible(self, user):
        if user.is_superuser:
            return self.all()
        else:
            return self.filter(
                Q(course__teacher=user) | Q(course__students=user, hidden=False)
            ).distinct()

    def filter_editable(self, user):
        if user.is_superuser:
            return self.all()
        else:
            return self.filter(course__teacher=user).distinct()


def upload_grader_file_path(assignment, _):  # pylint: disable=unused-argument
    assert assignment.id is not None
    if assignment.language == "P":
        return "assignment-{}/grader.py".format(assignment.id)
    else:
        return "assignment-{}/Grader.java".format(assignment.id)


class Assignment(models.Model):
    objects = AssignmentQuerySet.as_manager()

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

    LANGUAGES = (
        ("P", "Python 3"),
        ("J", "Java"),
    )
    language = models.CharField(max_length=1, choices=LANGUAGES, default="P")

    filename = models.CharField(max_length=50, default="main.py")

    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="assignments"
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

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("assignments:show", args=(self.id,))

    def submissions_from_student(self, student):
        return Submission.objects.filter(assignment=self, student=student)

    def make_assignment_dir(self) -> None:
        assignment_path = os.path.join(settings.MEDIA_ROOT, f"assignment-{self.id}")
        os.makedirs(assignment_path, exist_ok=True)

    def save_grader_file(self, grader_text: str) -> None:
        # Writing to files in directories not controlled by us without some
        # form of sandboxing is a security risk. Most notably, users can use symbolic
        # links to trick you into writing to another file, outside the directory.
        # they control.
        # This solution is very hacky, but we don't have another good way of
        # doing this.

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
                universal_newlines=True,
                check=True,
            )
        except FileNotFoundError as e:
            logger.error("Cannot run processes: %s", e)
            raise FileNotFoundError from e

    def list_files(self) -> List[Tuple[int, str, str, int, datetime.datetime]]:
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
        self.make_assignment_dir()

        fpath = os.path.join(settings.MEDIA_ROOT, "assignment-{}".format(self.id), file_name)

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
                universal_newlines=True,
                check=True,
            )
        except FileNotFoundError as e:
            logger.error("Cannot run processes: %s", e)
            raise FileNotFoundError from e

    def delete_file(self, file_id: int) -> None:
        self.make_assignment_dir()

        for i, item in enumerate(
            os.scandir(os.path.join(settings.MEDIA_ROOT, f"assignment-{self.id}"))
        ):
            if i == file_id and os.path.exists(item.path) and item.is_file():
                os.remove(item.path)
                return

    def compile_java_files(self) -> None:
        self.make_assignment_dir()

        fpath = os.path.join(settings.MEDIA_ROOT, "assignment-{}".format(self.id), "*.java")

        try:
            subprocess.run(
                [
                    "javac",
                    "-classpath",
                    "/usr/share/java/junit.jar:/usr/share/java/hamcrest.jar:.",
                    fpath,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                universal_newlines=True,
                check=True,
            )
        except FileNotFoundError as e:
            logger.error("Cannot run processes: %s", e)
            raise FileNotFoundError from e

    def check_rate_limit(self, student) -> None:
        now = timezone.localtime()

        if (
            Submission.objects.filter(
                date_submitted__gte=now
                - datetime.timedelta(minutes=self.submission_limit_interval),
                student=student,
            ).count()
            > self.submission_limit_count
        ):
            CooldownPeriod.objects.get_or_create(assignment=self, student=student)

    @property
    def venv_object_created(self):
        return Virtualenv.objects.filter(assignment=self).exists()

    @property
    def venv_fully_created(self):
        return Virtualenv.objects.filter(assignment=self, fully_created=True).exists()

    @property
    def grader_log_filename(self):
        return (
            upload_grader_file_path(self, "").rsplit(".", 1)[0] + ".log"
            if self.grader_file
            else None
        )

    @property
    def is_quiz(self):
        try:
            return self.quiz
        except:
            return False


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
                obj.delete()
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
            sum(lm.severity for lm in self.log_messages.filter(student=student))
            >= settings.QUIZ_ISSUE_THRESHOLD
        )

    def open_for_student(self, student):
        return not (self.locked_for_student(student) or self.ended_for_student(student))

    def locked_for_student(self, student):
        return self.issues_for_student(student) and self.action == "2"

    def ended_for_student(self, student):
        return self.log_messages.filter(student=student, content="Ended quiz").exists()


class LogMessage(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="log_messages")
    student = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="log_messages"
    )

    date = models.DateTimeField(auto_now_add=True)
    content = models.CharField(max_length=100)
    severity = models.IntegerField()

    def __str__(self):
        return f"{self.content} for {self.quiz}"

    def __repr__(self):
        return f"{self.content} for {self.quiz}"

    def get_absolute_url(self):
        return reverse(
            "assignments:student_submission", args=(self.quiz.assignment.id, self.student.id)
        )
