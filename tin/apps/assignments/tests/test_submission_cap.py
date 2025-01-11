from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from django.urls import reverse

from tin.tests import is_redirect, login


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
    assert is_redirect(response), f"Expected redirect, got {response}"

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
    assert is_redirect(response), f"Expected redirect, got {response}"

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
    assert is_redirect(response), f"Expected redirect, got {response}"
    response = submit()
    assert is_redirect(response), f"Expected redirect, got {response}"

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
    assert is_redirect(response), f"Expected redirect, got {response}"
    response = submit()
    assert is_redirect(response), f"Expected submission cap to not affect quizzes (got {response})"


@login("student")
def test_submission_cap_not_used(client, assignment):
    assignment.use_submission_cap = False
    assignment.submission_cap = 1
    assignment.submission_cap_after_due = 1
    assignment.due = datetime.today() + timedelta(days=1)
    assignment.save()

    def submit():
        url = "assignments:submit"
        return client.post(
            reverse(url, args=[assignment.id]),
            {"text": "print('I hate fun')"},
        )

    # all submissions should be fine because use_submission_cap is False
    response = submit()
    assert is_redirect(response), f"Expected redirect, got {response}"
    response = submit()
    assert is_redirect(response), f"Expected redirect, got {response}"


@login("teacher")
def test_create_student_override(client, assignment, student):
    response = client.post(
        reverse("assignments:create_student_override", args=[assignment.id, student.id]),
        {"submission_cap": 2},
    )
    assert is_redirect(response), f"Expected redirect, got {response}"

    override = assignment.find_student_override(student)
    assert override is not None
    assert override.submission_cap == 2
