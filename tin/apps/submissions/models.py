import logging
import os
import subprocess
from typing import Optional

from celery.canvas import Signature
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from ...sandboxing import get_assignment_sandbox_args
from .utils import decimal_repr

logger = logging.getLogger(__name__)


class SubmissionQuerySet(models.query.QuerySet):
    def filter_visible(self, user):
        if user.is_superuser:
            return self.all()
        else:
            return self.filter(
                Q(assignment__course__teacher=user)
                | Q(student=user) & Q(assignment__quiz__isnull=True)
            ).distinct()

    def filter_editable(self, user):
        if user.is_superuser:
            return self.all()
        else:
            return self.filter(Q(assignment__course__teacher=user) | Q(student=user)).distinct()


def upload_submission_file_path(submission, _):  # pylint: disable=unused-argument
    assert submission.assignment.id is not None
    if submission.assignment.language == "P":
        return "assignment-{}/{}/submission_{}.py".format(
            submission.assignment.id,
            slugify(submission.student.username),
            timezone.now().strftime("%Y%m%d_%H%M%S"),
        )
    else:
        return "assignment-{}/{}/submission_{}/{}".format(
            submission.assignment.id,
            slugify(submission.student.username),
            timezone.now().strftime("%Y%m%d_%H%M%S"),
            submission.assignment.filename,
        )


class Submission(models.Model):
    objects = SubmissionQuerySet.as_manager()

    assignment = models.ForeignKey(
        "assignments.Assignment", on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions"
    )

    date_submitted = models.DateTimeField(auto_now_add=True)
    last_run = models.DateTimeField(null=True, blank=True)

    has_been_graded = models.BooleanField(default=False)

    complete = models.BooleanField(default=False)

    # If this is set to True, it will make the Celery task kill the submission
    kill_requested = models.BooleanField(default=False)

    grader_pid = models.IntegerField(null=True, default=None, blank=True)
    grader_start_time = models.FloatField(null=True, default=None, blank=True)

    points_received = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)

    file = models.FileField(upload_to=upload_submission_file_path, null=True)

    grader_output = models.CharField(max_length=10 * 1024, blank=True)
    grader_errors = models.CharField(max_length=4 * 1024, blank=True)

    def __str__(self):
        return "{}{} [{}]: {} ({})".format(
            ("[INCOMPLETE] " if not self.complete else ""),
            self.student.username,
            self.date_submitted.strftime("%Y-%m-%d %H:%M:%S"),
            self.assignment.name,
            (self.grade_percent if self.has_been_graded else "not graded"),
        )

    def __repr__(self):
        return "{}{} [{}]: {} ({})".format(
            ("[INCOMPLETE] " if not self.complete else ""),
            self.student.username,
            self.date_submitted.strftime("%Y-%m-%d %H:%M:%S"),
            self.assignment.name,
            (self.grade_percent if self.has_been_graded else "not graded"),
        )

    def get_absolute_url(self):
        return reverse("submissions:show", args=[self.id])

    @property
    def is_on_time(self):
        return self.date_submitted <= self.assignment.due

    @property
    def points_possible(self):
        return self.assignment.points_possible

    @property
    def point_override(self):
        return sum(c.point_override for c in self.comments.all())

    @property
    def points(self):
        if self.points_received is None:
            return None
        return self.points_received + self.point_override

    @property
    def grade_percent(self):
        if self.points_received is None:
            return None
        return "{:.2%}".format(self.points / self.points_possible)

    @property
    def grade_percent_num(self):
        if self.points_received is None:
            return None
        return (self.points / self.points_possible) * 100

    @property
    def formatted_grade(self):
        if self.has_been_graded:
            return f"{decimal_repr(self.points)} / {decimal_repr(self.points_possible)} ({self.grade_percent})"
        return "Not graded"

    @property
    def file_path(self) -> Optional[str]:
        if self.file is None:
            return None

        return os.path.join(settings.MEDIA_ROOT, self.file.name)

    @property
    def wrapper_file_path(self) -> Optional[str]:
        if self.file is None:
            return None

        return os.path.join(
            settings.MEDIA_ROOT,
            os.path.dirname(self.file.name),
            "wrappers",
            os.path.basename(self.file.name),
        )

    @property
    def backup_file_path(self) -> Optional[str]:
        if self.file is None:
            return None

        return os.path.join(settings.MEDIA_ROOT, "submission-backups", self.file.name)

    def save_file(self, submission_text: str) -> None:
        # Writing to files in directories not controlled by us without some
        # form of sandboxing is a security risk. Most notably, users can use symbolic
        # links to trick you into writing to another file, outside the directory.
        # they control.
        # This solution is very hacky, but we don't have another good way of
        # doing this.

        fname = upload_submission_file_path(self, "")

        self.file.name = fname
        self.save()

        fpath = self.file_path

        os.makedirs(os.path.dirname(fpath), exist_ok=True)

        args = get_assignment_sandbox_args(
            ["sh", "-c", 'cat >"$1"', "sh", fpath],
            network_access=False,
            whitelist=[os.path.dirname(fpath)],
        )

        try:
            subprocess.run(
                args,
                input=submission_text,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                universal_newlines=True,
                check=True,
            )
        except FileNotFoundError as e:
            logger.error("Cannot run processes: %s", e)
            raise FileNotFoundError from e

    def create_backup_copy(self, submission_text: str) -> None:
        backup_fpath = self.backup_file_path

        if backup_fpath is None:
            raise ValueError

        os.makedirs(os.path.dirname(backup_fpath), mode=0o755, exist_ok=True)

        with open(backup_fpath, "w", encoding="utf-8") as f_obj:
            f_obj.write(submission_text)

    def rerun(self) -> Signature:
        from .tasks import run_submission

        self.complete = False
        self.has_been_graded = False
        self.last_run = timezone.now()
        self.save()

        return run_submission.s(self.id)

    @property
    def rerun_color(self):
        if self.last_run is None:
            return "black"
        if self.last_run > timezone.now() - timezone.timedelta(minutes=5):
            return "red"
        if self.last_run > timezone.now() - timezone.timedelta(days=1):
            return "orange"

    @property
    def channel_group_name(self) -> str:
        return "submission-{}".format(self.id)

    @property
    def is_latest(self):
        submissions = Submission.objects.filter(assignment=self.assignment, student=self.student)
        return submissions.latest() == self if submissions else False

    @property
    def is_published(self):
        return PublishedSubmission.objects.filter(
            assignment=self.assignment, student=self.student, submission=self
        ).exists()

    @property
    def is_latest_publish(self):
        latest_publish = PublishedSubmission.objects.filter(
            assignment=self.assignment, student=self.student
        )
        return latest_publish.latest().submission == self if latest_publish else False

    @property
    def published_submission(self):
        submissions = PublishedSubmission.objects.filter(
            student=self.student, assignment=self.assignment, submission=self
        )
        return submissions.first() if submissions else None

    def publish(self):
        if not self.is_published:
            PublishedSubmission.objects.create(
                assignment=self.assignment, student=self.student, submission=self
            )

    def unpublish(self):
        if self.is_published:
            PublishedSubmission.objects.filter(
                assignment=self.assignment, student=self.student, submission=self
            ).delete()

    class Meta:
        get_latest_by = "date_submitted"


class PublishedSubmission(models.Model):
    date = models.DateTimeField(auto_now_add=True)

    assignment = models.ForeignKey(
        "assignments.Assignment", on_delete=models.CASCADE, related_name="final_submissions"
    )
    student = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="final_submissions"
    )
    submission = models.OneToOneField(
        Submission, on_delete=models.CASCADE, related_name="final_submission"
    )

    @classmethod
    def get_published(cls, student, assignment):
        return cls.objects.filter(student=student, assignment=assignment).order_by("-date")

    class Meta:
        get_latest_by = "submission__date_submitted"


class Comment(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="comments")

    # Follows python slice syntax (0-indexed, inclusive:exclusive)
    start_char = models.IntegerField(validators=[MinValueValidator(0)])
    end_char = models.IntegerField(validators=[MinValueValidator(1)])

    date = models.DateTimeField(auto_now_add=True)
    text = models.CharField(max_length=1024)
    point_override = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
