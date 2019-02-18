from django.contrib.auth.signals import user_logged_in

from ..courses.models import StudentImport, StudentImportUser
from .models import User


def enroll(sender, user, request, **kwargs):
    try:
        import_user_object = StudentImportUser.objects.get_or_create(user = user.username)[0]
    except StudentImportUser.DoesNotExist:
        pass
    else:
        need_course_imports = StudentImport.objects.filter(students__user__iexact = user.username)
        for student_import in need_course_imports:
            student_import.course.students.add(User.objects.get(id = user.id))
            student_import.students.remove(import_user_object)
        import_user_object.delete()


user_logged_in.connect(enroll)
