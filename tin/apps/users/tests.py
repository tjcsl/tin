from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management import call_command


def test_create_debug_users():
    call_command("create_debug_users", noinput=True, verbosity=0)
    assert get_user_model().objects.filter(username="admin", is_superuser=True)
    assert get_user_model().objects.filter(username="student", is_student=True)
    assert get_user_model().objects.filter(username="teacher", is_teacher=True)
