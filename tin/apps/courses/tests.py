from __future__ import annotations

from django.urls import reverse

from tin.tests import is_login_redirect, is_redirect, teacher

from .models import Course


@teacher
def test_create_course(client, teacher) -> None:
    course_name = "Foundations of CS"
    response = client.post(
        reverse("courses:create"),
        {
            "name": [course_name],
            "teacher": [f"{teacher.id}"],
            "sort_assignments_by": ["due_date"],
        },
    )
    assert is_redirect(response)
    filter_ = Course.objects.filter(name__exact=course_name)
    assert filter_.count() == 1
    course = filter_.get()
    assert course.name == course_name


@teacher
def test_edit_course(client, course, teacher) -> None:
    old_name = course.name
    response = client.post(
        reverse("courses:edit", args=[course.id]),
        {
            "name": [f"{old_name} and Bezier Curves"],
            "teacher": [f"{teacher.id}"],
            "sort_assignments_by": ["due_date"],
        },
    )

    course.refresh_from_db()
    assert is_redirect(response)
    assert course.name == f"{old_name} and Bezier Curves"


def test_redirect(client) -> None:
    response = client.get(reverse("courses:index"))

    assert is_login_redirect(response)
