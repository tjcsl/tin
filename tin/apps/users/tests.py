import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command


@pytest.mark.no_autocreate_users
def test_create_debug_users():
    admin = get_user_model().objects.filter(username="admin", is_superuser=True)
    student = get_user_model().objects.filter(username="student", is_student=True)
    teacher = get_user_model().objects.filter(username="teacher", is_teacher=True)

    assert not admin.exists()
    assert not teacher.exists()
    assert not student.exists()

    call_command("create_debug_users", noinput=True, verbosity=0)

    assert admin.exists()
    assert teacher.exists()
    assert student.exists()
