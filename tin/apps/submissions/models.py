from django.db import models
from django.conf import settings

# Create your models here.

class Submission(models.Model):
    assignment = models.ForeignKey("assignments.Assignment", on_delete = models.CASCADE, related_name = "submissions")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE)
    
    date_submitted = models.DateTimeField(auto_now_add = True)

    points_received = models.DecimalField(max_digits = 4, decimal_places = 1)

    @property
    def is_on_time(self):
        return self.date_submitted <= self.assignment.due

    @property
    def points_possible(self):
        return self.assignment.points_possible

    @property
    def grade_percent(self):
        return "{}%".format(self.points_received / self.points_possible * 100)

