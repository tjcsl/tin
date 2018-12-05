from django.db import models
from django.conf import settings

from tin.apps.assignments.models import Assignment

# Create your models here.

class Course(models.Model):
    name = models.CharField(max_length = 50)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, null = True, on_delete = models.SET_NULL)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name = "courses")

