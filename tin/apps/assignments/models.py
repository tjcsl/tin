from django.core.validators import MinValueValidator
from django.db import models

from ..submissions.models import Submission
from ..venvs.models import Virtualenv


class AssignmentQuerySet(models.query.QuerySet):
    def filter_visible(self, user):
        if user.is_superuser:
            return self.all()
        elif user.is_teacher:
            return self.filter(course__teacher=user)
        else:
            return self.filter(course__students=user)

    def filter_editable(self, user):
        if user.is_superuser:
            return self.all()
        elif user.is_teacher:
            return self.filter(course__teacher=user)
        else:
            return self.none()


def upload_grader_file_path(assignment, filename):  # pylint: disable=unused-argument
    return "assignment-{}/grader.py".format(assignment.id)


class Assignment(models.Model):
    objects = AssignmentQuerySet.as_manager()

    name = models.CharField(max_length=50)
    description = models.CharField(max_length=4096)

    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="assignments"
    )

    points_possible = models.DecimalField(
        max_digits=6, decimal_places=3, validators=[MinValueValidator(1)]
    )

    assigned = models.DateTimeField(auto_now_add=True)
    due = models.DateTimeField()

    grader_file = models.FileField(upload_to=upload_grader_file_path, null=True)
    enable_grader_timeout = models.BooleanField(default=True)
    grader_timeout = models.IntegerField(default=300, validators=[MinValueValidator(10)])

    grader_has_network_access = models.BooleanField(default=False)

    has_network_access = models.BooleanField(default=False)

    def __str__(self):
        return "{} in {}".format(self.name, self.course)

    def __repr__(self):
        return "<{} in {}>".format(self.name, self.course)

    def submissions_from_student(self, student):
        return Submission.objects.filter(assignment=self, student=student)

    @property
    def venv_object_created(self):
        return Virtualenv.objects.filter(assignment=self).exists()

    @property
    def venv_fully_created(self):
        return Virtualenv.objects.filter(assignment=self, fully_created=True).exists()

    @property
    def grader_log_filename(self):
        return self.grader_file.name[:-3] + ".log" if self.grader_file else None
