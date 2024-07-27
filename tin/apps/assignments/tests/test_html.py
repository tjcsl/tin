from __future__ import annotations

import pytest
from django.urls import reverse

from tin.tests import Html, login

from .. import views


@login("student")
@pytest.mark.parametrize(
    ("course_perm", "is_archived", "visible"),
    (
        ("-", False, True),
        ("r", False, True),
        ("w", False, True),
        ("-", True, False),
        ("r", True, False),
        ("w", True, True),
    ),
)
def test_can_submit_assignment(
    client,
    course,
    assignment,
    course_perm: str,
    is_archived: bool,
    visible: bool,
):
    course.archived = is_archived
    course.permission = course_perm
    course.save()
    response = client.get(
        reverse("assignments:show", args=[assignment.id]),
    )
    html = Html.from_response(response)
    assert html.has_button("Submit") is visible


@pytest.mark.parametrize(
    ("user", "visible"),
    (
        ("student", False),
        ("teacher", True),
    ),
)
def test_can_create_assignment(rf, course, student, teacher, user, visible):
    user_map = {
        "student": student,
        "teacher": teacher,
    }
    request = rf.get(
        reverse("assignments:add", args=[course.id]),
    )
    request.user = user_map[user]
    response = views.create_view(request, course.id)
    html = Html.from_response(response)
    assert html.has_button("Create") is visible


@login("student")
def test_can_submit_assignment_from_form(client, assignment):
    response = client.get(
        reverse("assignments:submit", args=[assignment.id]),
    )
    html = Html.from_response(response)
    # no grader has been added yet
    assert not html.has_button("Submit")
    assignment.save_grader_file("print('Instanced Rendering OP')")

    response = client.get(
        reverse("assignments:submit", args=[assignment.id]),
    )
    html = Html.from_response(response)
    assert html.has_button("Submit")
