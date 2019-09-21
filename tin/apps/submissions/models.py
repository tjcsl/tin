import os
from typing import Optional

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

# Create your models here.


def upload_submission_file_path(submission, filename):  # pylint: disable=unused-argument
    return "assignment-{}/{}/submission_{}.py".format(
        submission.assignment.id,
        slugify(submission.student.username),
        timezone.now().strftime("%Y%m%d_%H%M%S"),
    )


class Submission(models.Model):
    assignment = models.ForeignKey(
        "assignments.Assignment", on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    date_submitted = models.DateTimeField(auto_now_add=True)

    has_been_graded = models.BooleanField(default=False)

    complete = models.BooleanField(default=False)

    grader_pid = models.IntegerField(null=True, default=None, blank=True)
    grader_start_time = models.FloatField(null=True, default=None, blank=True)

    points_received = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)

    file = models.FileField(upload_to=upload_submission_file_path, null=True)

    grader_output = models.CharField(max_length=10 * 1024, blank=True)
    grader_errors = models.CharField(max_length=2 * 1024, blank=True)

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

    def create_backup_copy(self, submission_text: str) -> None:
        backup_fpath = self.backup_file_path

        if backup_fpath is None:
            raise ValueError

        os.makedirs(os.path.dirname(backup_fpath), mode=0o755, exist_ok=True)

        with open(backup_fpath, "w") as f_obj:
            f_obj.write(submission_text)

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
