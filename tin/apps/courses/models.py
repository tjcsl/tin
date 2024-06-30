from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse


class CourseQuerySet(models.query.QuerySet):
    """Provide filtering utilities for courses."""

    def filter_visible(self, user):
        """Filters if a course is visible to a user.

        Admins can see all courses, teachers can only
        see course they teach, and students can only see non-archived
        courses OR courses that have permission "r" or "w"
        """
        if user.is_superuser:
            return self.all()
        else:
            return self.filter(
                Q(teacher=user)
                | (Q(students=user) & (Q(archived=False) | Q(permission="r") | Q(permission="w")))
            ).distinct()

    def filter_editable(self, user):
        """Filter courses a user can edit."""
        if user.is_superuser:
            return self.all()
        else:
            return self.filter(teacher=user).distinct()


class Course(models.Model):
    """A TJHSST Course

    e.g. Foundations of Computer Science
    """

    SORT_BY = (("due_date", "Due Date"), ("name", "Name"))
    PERMISSIONS = (
        ("w", "view and submit assignments"),
        ("r", "view assignments"),
        ("-", "see nothing"),
    )

    name = models.CharField(max_length=50, blank=False)
    teacher = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=False,
        related_name="taught_courses",
    )
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="courses", blank=True)

    created = models.DateTimeField(auto_now_add=True)

    sort_assignments_by = models.CharField(max_length=30, choices=SORT_BY, default="due_date")

    archived = models.BooleanField(default=False)
    permission = models.CharField(max_length=1, choices=PERMISSIONS, default="r")

    objects = CourseQuerySet.as_manager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("courses:show", args=[self.id])

    def __repr__(self):
        return self.name

    def get_teacher_str(self) -> str:
        """Get a string of the last names of all teachers in a course"""
        return ", ".join(t.last_name for t in self.teacher.all())

    def is_student_in_course(self, user) -> bool:
        """Check if a student is registered in the course"""
        return self.students.contains(user)

    def is_only_student_in_course(self, user) -> bool:
        """Check if a user is the only student in a course"""
        return self.is_student_in_course(user) and not (
            user.is_superuser or user in self.teacher.all()
        )


class Period(models.Model):
    """A Period, or a Block

    e.g. Period 7
    """

    name = models.CharField(max_length=50, blank=False)
    course = models.ForeignKey(
        Course, null=True, on_delete=models.CASCADE, related_name="period_set"
    )

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="taught_periods",
    )

    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="periods", blank=True)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("courses:students", args=[self.course.id]) + f"?period={self.id}"

    def __repr__(self):
        return self.name


class StudentImportUser(models.Model):
    """A student that is to be added to a course when they log in"""

    user = models.CharField(max_length=15, unique=True)

    class Meta:
        verbose_name = "Imported Student"

    def __str__(self):
        return self.user

    def __repr__(self):
        return self.user


class StudentImport(models.Model):
    students = models.ManyToManyField(StudentImportUser, related_name="users")
    course = models.OneToOneField(Course, unique=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Student Import"

    def __str__(self):
        return f"Import into {self.course.name}"

    def get_absolute_url(self):
        return reverse("courses:import_students", args=[self.course.id])

    def __repr__(self):
        return f"Import into {self.course.name}"

    def queue_users(self, usernames):
        """Add usernames to a queue of students to add to a course"""
        for username in usernames:
            import_user_object = StudentImportUser.objects.get_or_create(user=username)[0]
            self.students.add(import_user_object)
        self.save()
