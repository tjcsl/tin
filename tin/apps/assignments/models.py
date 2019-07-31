import datetime

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

from ..submissions.models import Submission


def upload_grader_file_path(assignment, filename):
    return "assignment-{}/grader.py".format(assignment.id)


class Assignment(models.Model):
    name = models.CharField(max_length = 50)
    description = models.CharField(max_length = 255)

    course = models.ForeignKey("courses.Course", on_delete = models.CASCADE, related_name = "assignments")

    points_possible = models.DecimalField(
        max_digits = 6,
        decimal_places = 3,
        validators = [
            MinValueValidator(1),
        ],
    )

    assigned = models.DateTimeField(auto_now_add = True)
    due = models.DateTimeField()

    requested_num_containers = models.IntegerField(default = -1)

    grader_file = models.FileField(upload_to = upload_grader_file_path, null = True)
    enable_grader_timeout = models.BooleanField(default = False)
    grader_timeout = models.IntegerField(default = 300, validators = [MinValueValidator(10)])

    has_network_access = models.BooleanField(default = False)

    def __str__(self):
        return "{} in {}".format(self.name, self.course)

    def __repr__(self):
        return "<{} in {}>".format(self.name, self.course)

    def submissions_from_student(self, student):
        return Submission.objects.filter(assignment = self, student = student)

    @property
    def preferred_num_containers(self):
        if self.requested_num_containers is not None and self.requested_num_containers > 0:
            return min(self.requested_num_containers, 20)

        now = timezone.localtime()
        if now < self.due:
            return 4
        elif now < self.due + datetime.timedelta(days = 2):
            return 3
        elif now < self.due + datetime.timedelta(days = 4):
            return 2
        else:
            return 1

    @property
    def grader_log_filename(self):
        return (self.grader_file.name[:-3] + ".log" if self.grader_file else None)

