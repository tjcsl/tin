from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.text import slugify

# Create your models here.


def upload_submission_file_path(submission, filename):
    return "assignment-{}/{}/submission_{}.py".format(submission.assignment.id, slugify(submission.student.username), timezone.now().strftime("%Y%m%d_%H%M%S"))


class Submission(models.Model):
    assignment = models.ForeignKey("assignments.Assignment", on_delete = models.CASCADE, related_name = "submissions")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE)

    date_submitted = models.DateTimeField(auto_now_add = True)

    has_been_graded = models.BooleanField(default = False)

    complete = models.BooleanField(default = False)

    points_received = models.DecimalField(max_digits = 4, decimal_places = 1, null = True, blank = True)

    file = models.FileField(upload_to = upload_submission_file_path, null = True)

    grader_output = models.CharField(max_length = 10 * 1024, blank = True)
    grader_errors = models.CharField(max_length = 2 * 1024, blank = True)

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
        return "{}%".format(self.points_received / self.points_possible * 100)

    @property
    def formatted_grade(self):
        if self.has_been_graded:
            return "{}/{} ({})".format(self.points_received, self.points_possible, self.grade_percent)
        return "Not graded"

