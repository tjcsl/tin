from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models


class CourseQuerySet(models.query.QuerySet):
    def filter_visible(self, user):
        if user.is_superuser:
            return self.all()
        elif user.is_teacher:
            return self.filter(teacher=user)
        else:
            return self.filter(students=user)

    def filter_editable(self, user):
        if user.is_superuser:
            return self.all()
        elif user.is_teacher:
            return self.filter(teacher=user)
        else:
            return self.none()


class Course(models.Model):
    SORT_BY = (("due_date", "Due Date"), ("name", "Name"))

    objects = CourseQuerySet.as_manager()

    name = models.CharField(max_length=50, blank=False)
    teacher = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=False,
        related_name="taught_courses",
    )
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="courses", blank=True)

    created = models.DateTimeField(auto_now_add=True)

    sort_assignments_by = models.CharField(max_length=30, choices=SORT_BY, default="due_date")

    def __str__(self):
        return "{} (teachers: {})".format(
            self.name, ", ".join((str(t) for t in self.teacher.all()))
        )

    def __repr__(self):
        return "<{} (teachers: {})>".format(
            self.name, ", ".join((str(t) for t in self.teacher.all()))
        )

    def get_teacher_str(self):
        return ", ".join((t.last_name for t in self.teacher.all()))


class Period(models.Model):
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
        return "{} ({})".format(self.name, self.teacher.last_name)

    def __repr__(self):
        return "{} (course: {}, teacher: {})".format(self.name, self.course, self.teacher)


class StudentImportUser(models.Model):
    user = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.user


class StudentImport(models.Model):
    students = models.ManyToManyField(StudentImportUser, related_name="users")
    course = models.OneToOneField(Course, unique=True, on_delete=models.CASCADE)

    def __str__(self):
        return "{} student(s) unimported ({})".format(self.students.count(), self.course.name)

    def queue_users(self, usernames):
        for username in usernames:
            import_user_object = StudentImportUser.objects.get_or_create(user=username)[0]
            self.students.add(import_user_object)
        self.save()
