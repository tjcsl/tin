from django.db import models
from django.core.validators import MinValueValidator

from ..submissions.models import Submission


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

    def __str__(self):
        return "{} in {}".format(self.name, self.course)

    def __repr__(self):
        return "<{} in {}>".format(self.name, self.course)

    def submissions_from_student(self, student):
        return Submission.objects.filter(assignment = self, student = student)
