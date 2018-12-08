from django.db import models
from django.conf import settings


class Course(models.Model):
    name = models.CharField(max_length = 50)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, null = True, on_delete = models.SET_NULL)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name = "courses")

    def __str__(self):
        return "{} (teacher: {})".format(self.name, self.teacher)

    def __repr__(self):
        return "<{} (teacher: {})>".format(self.name, self.teacher)
