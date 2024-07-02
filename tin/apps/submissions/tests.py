from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from tin.tests import is_redirect, login

if TYPE_CHECKING:
    from django.test import Client

    from ..courses.models import Course
    from .models import Submission


@login("student")
@pytest.mark.parametrize(
    ("perm", "hidden", "archived"),
    (
        # normal
        ("-", False, False),
        ("r", False, False),
        ("w", False, False),
        # archived
        ("-", True, True),
        ("r", False, True),
        ("w", False, True),
    ),
)
def test_see_submission_after_archived(
    client: Client, course: Course, submission: Submission, perm: str, hidden: bool, archived: bool
):
    course.permission = perm
    course.archived = archived
    course.save()

    response = client.get(reverse("submissions:show", args=[submission.id]))
    assert (response.status_code == 404) is hidden


@login("student")
def test_student_requests_kill(client: Client, submission: Submission):
    response = client.post(reverse("submissions:kill", args=[submission.id]))
    submission.refresh_from_db()
    assert is_redirect(response)
    assert submission.kill_requested


@login("teacher")
def test_teacher_requests_kill(client: Client, submission: Submission):
    response = client.post(reverse("submissions:kill", args=[submission.id]))
    submission.refresh_from_db()
    assert is_redirect(response)
    assert submission.kill_requested
