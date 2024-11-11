from __future__ import annotations

import io

from django.conf import settings
from django.urls import reverse

from tin.tests import is_redirect, login, str_to_html


@login("teacher")
def test_grader_view(client, assignment):
    sample_grader = io.BytesIO(b"some text")
    response = client.post(
        reverse("assignments:manage_grader", args=[assignment.id]), {"grader_file": sample_grader}
    )

    assert is_redirect(response)


@login("teacher")
def test_incorrect_grader(client, assignment):
    binary_data = io.BytesIO(b"b" * (settings.SUBMISSION_SIZE_LIMIT + 1))
    response = client.post(
        reverse("assignments:manage_grader", args=[assignment.id]), {"grader_file": binary_data}
    )

    error = str_to_html(
        "That file's too large. Are you sure it's a Python program?",
    )
    assert error in response.content.decode("utf-8")


@login("teacher")
def test_download_grader(client, assignment):
    response = client.post(
        reverse("assignments:download_grader", args=[assignment.id]),
    )
    assert response.status_code == 404

    code = "print('hello, world')"
    assignment.save_grader_file(code)
    assignment.save()

    response = client.post(
        reverse("assignments:download_grader", args=[assignment.id]),
    )

    assert response.status_code == 200
    assert response.content.decode("utf-8") == code


def test_grader_save_file(assignment):
    assignment.save_grader_file("print('hello, world')")
    assert assignment.grader_exists()
