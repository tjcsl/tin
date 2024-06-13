from __future__ import annotations

import pytest
from django.urls import reverse

from tin.tests import login


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
    client, course, submission, perm: str, hidden: bool, archived: bool
):
    course.permission = perm
    course.archived = archived
    course.save()

    response = client.get(reverse("submissions:show", args=[submission.id]))
    assert (response.status_code == 404) is hidden
