from __future__ import annotations

import pytest
from django.urls import reverse

from tin.tests import Html, login


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
