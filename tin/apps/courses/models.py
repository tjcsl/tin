from django.conf import settings
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
    objects = CourseQuerySet.as_manager()

    name = models.CharField(max_length=50, blank=False)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name="taught_courses",
    )
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="courses", blank=True)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} (teacher: {})".format(self.name, self.teacher)

    def __repr__(self):
        return "<{} (teacher: {})>".format(self.name, self.teacher)


class Period(models.Model):
    name = models.CharField(max_length=50, blank=False)
    course = models.ForeignKey(
        Course, null=True, on_delete=models.CASCADE, related_name="period_set"
    )

    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="periods", blank=True)

    def __str__(self):
        return "{} (course: {})".format(self.name, self.course)

    def __repr__(self):
        return "{} (course: {})".format(self.name, self.course)


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
