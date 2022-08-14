import datetime
import os
import subprocess

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from ...sandboxing import get_assignment_sandbox_args
from ..submissions.models import Submission
from ..venvs.models import Virtualenv


class Folder(models.Model):
    name = models.CharField(max_length=50)

    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="folders")

    def __str__(self):
        return self.name


class AssignmentQuerySet(models.query.QuerySet):
    def filter_visible(self, user):
        if user.is_superuser:
            return self.all()
        else:
            return self.filter(Q(course__teacher=user) | Q(course__students=user, hidden=False))

    def filter_editable(self, user):
        if user.is_superuser:
            return self.all()
        else:
            return self.filter(course__teacher=user)


def upload_grader_file_path(assignment, filename):  # pylint: disable=unused-argument
    assert assignment.id is not None
    return "assignment-{}/grader.py".format(assignment.id)


class Assignment(models.Model):
    objects = AssignmentQuerySet.as_manager()

    name = models.CharField(max_length=50)
    folder = models.ForeignKey(
        Folder, on_delete=models.SET_NULL, default=None, null=True, blank=True
    )
    description = models.CharField(max_length=4096)

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
        return "{} in {}".format(self.name, self.course)

    def __repr__(self):
        return "<{} in {}>".format(self.name, self.course)

    def submissions_from_student(self, student):
        return Submission.objects.filter(assignment=self, student=student)

    def save_grader_file(self, grader_text: str) -> None:
        # Writing to files in directories not controlled by us without some
        # form of sandboxing is a security risk. Most notably, users can use symbolic
        # links to trick you into writing to another file, outside the directory.
        # they control.
        # This solution is very hacky, but we don't have another good way of
        # doing this.

        fname = upload_grader_file_path(self, "")

        self.grader_file = fname
        self.grader_file.name = fname
        self.save()

        fpath = os.path.join(settings.MEDIA_ROOT, self.grader_file.name)

        os.makedirs(os.path.dirname(fpath), exist_ok=True)

        args = get_assignment_sandbox_args(
            ["sh", "-c", 'cat >"$1"', "sh", fpath],
            network_access=False,
            whitelist=[os.path.dirname(fpath)],
        )

        subprocess.run(
            args,
            input=grader_text,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        )

    def check_rate_limit(self, student) -> None:
        now = timezone.localtime()

        if (
            Submission.objects.filter(
                date_submitted__gte=now - datetime.timedelta(minutes=self.submission_limit_interval)
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
        return self.grader_file.name[:-3] + ".log" if self.grader_file else None

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

    def __str__(self):
        return f"Quiz for {self.assignment}"

    def locked_for_student(self, student):
        return sum(lm.severity for lm in self.log_messages.filter(student=student)) >= settings.QUIZ_LOCK_THRESHOLD

    def ended_for_student(self, student):
        return self.log_messages.filter(student=student, content="Ended quiz").exists()


class LogMessage(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="log_messages"
    )
    student = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="log_messages"
    )

    date = models.DateTimeField(auto_now_add=True)
    content = models.CharField(max_length=100)
    severity = models.IntegerField()

    def __str__(self):
        return f"{self.content} for {self.quiz}"
