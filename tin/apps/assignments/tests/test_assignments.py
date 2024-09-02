from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta

import pytest
from django.urls import reverse

from tin.tests import is_redirect, login


@login("teacher")
def test_create_assignment(client, course) -> None:
    data = {
        "name": "Write a Vertex Shader",
        "description": "See https://learnopengl.com/Getting-started/Shaders",
        "language": "P",
        "filename": "vertex.glsl",
        "points_possible": "300",
        "due": "04/16/2025",
        "grader_timeout": "300",
        "submission_limit_count": "90",
        "submission_limit_interval": "30",
        "submission_limit_cooldown": "30",
        "is_quiz": False,
        "quiz_action": "2",
        "submission_cap": "100",
        "submission_cap_after_due": "100",
        "use_submission_cap": False,
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


@login("student")
def test_submission_cap(client, assignment):
    assignment.use_submission_cap = True
    assignment.submission_cap = 1
    assignment.submission_cap_after_due = 1
    assignment.due = datetime.today() + timedelta(days=1)
    assignment.save()
    code = "print('hello, world')"
    assignment.save_grader_file(code)

    def submit():
        url = "assignments:submit"
        return client.post(
            reverse(url, args=[assignment.id]),
            {"text": "print('I hate fun')"},
        )

    response = submit()
    assert response.status_code == 302, f"Expected status code 302, got {response}"

    # but now we've passed the cap
    response = submit()
    assert response.status_code == 403, f"Expected status code 403, got {response}"


@login("student")
def test_submission_cap_overdue(client, assignment):
    assignment.use_submission_cap = True
    assignment.submission_cap = 10000
    assignment.submission_cap_after_due = 1
    assignment.due = datetime.today() - timedelta(days=1)
    assignment.save()
    code = "print('hello, world')"
    assignment.save_grader_file(code)

    def submit():
        url = "assignments:submit"
        return client.post(
            reverse(url, args=[assignment.id]),
            {"text": "print('I hate fun')"},
        )

    response = submit()
    assert response.status_code == 302, f"Expected status code 302, got {response}"

    # but now we've passed the cap
    response = submit()
    assert response.status_code == 403, f"Expected status code 403, got {response}"


@login("student")
@pytest.mark.parametrize(
    "due", (datetime.today() - timedelta(days=1), datetime.today() + timedelta(days=1))
)
def test_submission_cap_with_override(client, assignment, student, due):
    """Test the submission cap with a per student override.

    The override should take place regardless of the due date of the :class:`.Assignment`.
    """
    assignment.due = due
    assignment.use_submission_cap = True
    assignment.submission_cap = 1
    assignment.submission_cap_after_due = 1
    assignment.save()
    code = "print('hello, world')"
    assignment.save_grader_file(code)

    # add student override
    assignment.student_overrides.create(student=student, submission_cap=2)

    def submit():
        url = "assignments:submit"
        return client.post(
            reverse(url, args=[assignment.id]),
            {"text": "print('I hate fun')"},
        )

    # first and second submission should be fine
    response = submit()
    assert response.status_code == 302, f"Expected status code 302, got {response}"
    response = submit()
    assert response.status_code == 302, f"Expected status code 302, got {response}"

    # but now we've passed the cap for the student
    response = submit()
    assert response.status_code == 403, f"Expected status code 403, got {response}"


@login("student")
def test_submission_cap_on_quiz(client, quiz):
    quiz.use_submission_cap = True
    quiz.submission_cap = 1
    quiz.submission_cap_after_due = 1
    quiz.save()
    code = "print('hello, world')"
    quiz.save_grader_file(code)

    def submit():
        url = "assignments:quiz"
        return client.post(
            reverse(url, args=[quiz.id]),
            {"text": "print('I hate fun')"},
        )

    response = submit()
    assert response.status_code == 302, f"Expected status code 302, got {response}"
    response = submit()
    assert (
        response.status_code == 302
    ), f"Expected submission cap to not affect quizzes (got {response})"
