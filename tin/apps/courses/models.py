from django.db import models
from django.conf import settings


class Course(models.Model):
    name = models.CharField(max_length = 50)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, null = True, on_delete = models.SET_NULL)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name = "courses")

    created = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return "{} (teacher: {})".format(self.name, self.teacher)

    def __repr__(self):
        return "<{} (teacher: {})>".format(self.name, self.teacher)


class StudentImportUser(models.Model):
    user = models.CharField(max_length = 15, unique = True)

    def __str__(self):
        return self.user


class StudentImport(models.Model):
    students = models.ManyToManyField(StudentImportUser, related_name = "users")
    course = models.ForeignKey(Course, null=True, unique = True, on_delete = models.SET_NULL)

    def __str__(self):
        return "{} student(s) unimported ({})".format(self.students.count(), self.course.name)

    def queue_users(self, usernames):
        for username in usernames:
            import_user_object = StudentImportUser.objects.get_or_create(user = username)[0]
            self.students.add(import_user_object)
        self.save()
