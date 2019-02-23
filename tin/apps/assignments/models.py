from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify

from ..submissions.models import Submission


def upload_grader_file_path(assignment, filename):
    return "{}/grader_{}_{}".format(slugify(assignment.name), assignment.course.id, assignment.id)


class Assignment(models.Model):
    name = models.CharField(max_length = 50)
    description = models.CharField(max_length = 255)

    course = models.ForeignKey("courses.Course", on_delete = models.CASCADE, related_name = "assignments")

    points_possible = models.DecimalField(
        max_digits = 4,
        decimal_places = 1,
        validators = [
            MinValueValidator(1),
        ],
    )

    assigned = models.DateTimeField(auto_now_add = True)
    due = models.DateTimeField()

    grader_file = models.FileField(upload_to = upload_grader_file_path, null = True)
    enable_grader_timeout = models.BooleanField(default = False)
    grader_timeout = models.IntegerField(default = 300, validators = [MinValueValidator(10)])

    def __str__(self):
        return "{} in {}".format(self.name, self.course)

    def __repr__(self):
        return "<{} in {}>".format(self.name, self.course)

    def submissions_from_student(self, student):
        return Submission.objects.filter(assignment = self, student = student)
