from django.contrib.auth.signals import user_logged_in

from ..courses.models import StudentImport, StudentImportUser
from .models import User


def enroll(sender, user, request, **kwargs):
    need_course_imports = StudentImport.objects.filter(students__user__iexact=user.username)
    for student_import in need_course_imports:
        student_import.course.students.add(User.objects.get(id=user.id))
        student_import.students.remove(StudentImportUser.objects.get(user=user.username))

user_logged_in.connect(enroll)
