from __future__ import annotations

import pytest
from django.urls import reverse

from tin.tests import is_login_redirect, is_redirect, login

from .models import Course


@login("teacher")
def test_create_course(client, teacher) -> None:
    course_name = "Foundations of CS"
    response = client.post(
        reverse("courses:create"),
        {
            "name": [course_name],
            "teacher": [f"{teacher.id}"],
            "sort_assignments_by": ["due_date"],
            "archived": False,
            "permission": "r",
        },
    )
    assert is_redirect(response)
    filter_ = Course.objects.filter(name__exact=course_name)
    assert filter_.count() == 1
    course = filter_.get()
    assert course.name == course_name


@login("teacher")
def test_edit_course(client, course, teacher) -> None:
    old_name = course.name
    response = client.post(
        reverse("courses:edit", args=[course.id]),
        {
            "name": [f"{old_name} and Bezier Curves"],
            "teacher": [f"{teacher.id}"],
            "sort_assignments_by": ["due_date"],
            "archived": False,
            "permission": "r",
        },
    )

    course.refresh_from_db()
    assert is_redirect(response)
    assert course.name == f"{old_name} and Bezier Curves"


def test_redirect(client) -> None:
    response = client.get(reverse("courses:index"))

    assert is_login_redirect(response)


@login("student")
@pytest.mark.parametrize(
    ("perm", "coursecode", "assignmentcode", "submitcode"),
    (
        ("-", 404, 404, 404),
        ("r", 200, 200, 404),
        ("rw", 200, 200, 200),
    ),
)
def test_access_hidden_archived_course(
    client, course, assignment, perm, coursecode, assignmentcode, submitcode
):
    course.archived = True
    course.permission = perm
    course.save()
    response = client.get(
        reverse("courses:show", args=[course.id]),
    )
    assert response.status_code == coursecode

    response = client.get(reverse("assignments:show", args=[assignment.id]))
    assert response.status_code == assignmentcode

    response = client.get(reverse("assignments:submit", args=[assignment.id]))
    assert response.status_code == submitcode
