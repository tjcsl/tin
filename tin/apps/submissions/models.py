import os
import subprocess
from typing import Optional

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

from ...sandboxing import get_assignment_sandbox_args

# Create your models here.


class SubmissionQuerySet(models.query.QuerySet):
    def filter_visible(self, user):
        if user.is_superuser:
            return self.all()
        else:
            return self.filter(
                Q(assignment__course__teacher=user) | Q(student=user)
            ).distinct()

    def filter_editable(self, user):
        if user.is_superuser:
            return self.all()
        else:
            return self.filter(
                Q(assignment__course__teacher=user) | Q(student=user)
            ).distinct()


def upload_submission_file_path(submission, filename):  # pylint: disable=unused-argument
    assert submission.assignment.id is not None
    return "assignment-{}/{}/submission_{}.py".format(
        submission.assignment.id,
        slugify(submission.student.username),
        timezone.now().strftime("%Y%m%d_%H%M%S"),
    )


class Submission(models.Model):
    objects = SubmissionQuerySet.as_manager()

    assignment = models.ForeignKey(
        "assignments.Assignment", on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    date_submitted = models.DateTimeField(auto_now_add=True)

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

    @property
    def is_on_time(self):
        return self.date_submitted <= self.assignment.due

    @property
    def points_possible(self):
        return self.assignment.points_possible

    @property
    def grade_percent(self):
        if self.points_received is None:
            return None
        return "{:.2%}".format(self.points_received / self.points_possible)

    @property
    def formatted_grade(self):
        if self.has_been_graded:
            return "{}/{} ({})".format(
                self.points_received, self.points_possible, self.grade_percent
            )
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

        self.file = fname
        self.file.name = fname

        fpath = self.file_path

        args = get_assignment_sandbox_args(
            ["mkdir", "-p", "--", os.path.dirname(fpath)],
            network_access=False,
            whitelist=[os.path.dirname(os.path.dirname(fpath))],
        )

        subprocess.run(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        )

        args = get_assignment_sandbox_args(
            ["sh", "-c", 'cat >"$1"', "sh", fpath],
            network_access=False,
            whitelist=[os.path.dirname(fpath)],
        )

        subprocess.run(
            args,
            input=submission_text,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        )

    def create_backup_copy(self, submission_text: str) -> None:
        backup_fpath = self.backup_file_path

        if backup_fpath is None:
            raise ValueError

        os.makedirs(os.path.dirname(backup_fpath), mode=0o755, exist_ok=True)

        with open(backup_fpath, "w") as f_obj:
            f_obj.write(submission_text)

    @property
    def channel_group_name(self) -> str:
        return "submission-{}".format(self.id)

    def __str__(self):
        return "{}{} [{}]: {} ({})".format(
            ("[INCOMPLETE] " if not self.complete else ""),
            self.student.username,
            self.date_submitted.strftime("%Y-%m-%d %H:%M:%S"),
            self.assignment.name,
            (self.grade_percent if self.has_been_graded else "not graded"),
        )

    def __repr__(self):
        return "<{}>".format(self)
