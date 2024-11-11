from __future__ import annotations

import csv
import io

import pytest
from django.urls import reverse

from tin.tests import is_redirect, login


@login("teacher")
def test_create_assignment(client, course, python) -> None:
    data = {
        "name": "Write a Vertex Shader",
        "description": "See https://learnopengl.com/Getting-started/Shaders",
        "filename": "vertex.glsl",
        "points_possible": "300",
        "due": "04/16/2025",
        "grader_timeout": "300",
        "submission_limit_count": "90",
        "submission_limit_interval": "30",
        "submission_limit_cooldown": "30",
        "is_quiz": False,
        "quiz_action": "2",
        "language_details": python.id,
    }
    response = client.post(
        reverse("assignments:add", args=[course.id]),
        data,
    )
    assert is_redirect(response)
    assignment_set = course.assignments.filter(name__exact=data["name"])
    assert assignment_set.count() == 1


@login("teacher")
def test_delete_assignment(client, assignment):
    response = client.post(reverse("assignments:delete", args=[assignment.id]))
    assert is_redirect(response)

    with pytest.raises(type(assignment).DoesNotExist):
        assignment.refresh_from_db()


@login("student")
def test_submit_assignment_with_text(client, assignment):
    response = client.post(
        reverse("assignments:submit", args=[assignment.id]), {"text": "print('I hate CSS')"}
    )

    assert is_redirect(response)
    assert assignment.submissions.count() == 1


@login("student")
def test_submit_assignment_with_file(client, assignment):
    response = client.post(
        reverse("assignments:submit", args=[assignment.id]),
        {"file": io.BytesIO(b"print('I hate CSS')")},
    )

    assert is_redirect(response)
    assert assignment.submissions.count() == 1


@login("teacher")
def test_csv_of_missing_assignment(client, assignment, student):
    assignment.submissions.create(student=student)
    response = client.get(
        reverse("assignments:scores_csv", args=[assignment.id]), {"period": "all"}
    )
    reader = csv.reader(io.StringIO(response.content.decode("utf-8")))
    next(reader)  # skip row with headers
    row = next(reader)
    assert row is not None
    (full_name, username, _period, raw, final, formatted) = row
    assert student.full_name == full_name
    assert student.username == username
    assert raw == "NG"
    assert final == "NG"
    assert formatted == "NG"


@login("teacher")
def test_csv_of_missing_assignment_graded(client, assignment, student):
    max_points = float(assignment.points_possible) / 2
    assignment.submissions.create(
        student=student,
        has_been_graded=True,
        points_received=max_points,
    )
    response = client.get(
        reverse("assignments:scores_csv", args=[assignment.id]), {"period": "all"}
    )
    reader = csv.reader(io.StringIO(response.content.decode("utf-8")))
    next(reader)  # skip initial row with headers
    row = next(reader)
    assert row is not None
    (full_name, username, _period, raw, final, formatted) = row
    assert student.full_name == full_name
    assert student.username == username
    assert float(raw) == max_points
    assert float(final) == max_points
    assert formatted == "150 / 300 (50.00%)"
