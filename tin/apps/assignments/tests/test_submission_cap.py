from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from tin.tests import is_redirect, login

yesterday = timezone.now() - timedelta(days=1)
tomorrow = timezone.now() + timedelta(days=1)


@login("student")
def test_submission_cap(client, assignment):
    assignment.submission_caps.create(submission_cap=1)
    assignment.due = tomorrow
    assignment.save()
    code = "print('hello, world')"
    assignment.save_grader_file(code)

    def submit():
        return client.post(
            reverse("assignments:submit", args=[assignment.id]),
            {"text": "print('I hate fun')"},
        )

    response = submit()
    assert is_redirect(response), f"Expected redirect, got {response}"

    # but now we've passed the cap
    response = submit()
    assert response.status_code == 403, f"Expected status code 403, got {response}"


@login("student")
def test_submission_cap_overdue(client, assignment):
    assignment.submission_caps.create(submission_cap_after_due=1)
    assignment.due = yesterday
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
def test_submission_cap_only_after_due(client, assignment):
    assignment.submission_caps.create(submission_cap_after_due=1)
    assignment.due = tomorrow
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

    response = submit()
    assert is_redirect(response), f"Expected infinite submissions before due date (got {response})"


@login("student")
def test_submission_cap_only_before(client, assignment):
    """Test the submission cap when due date has passed but submission_cap_after_due is not set."""
    assignment.submission_caps.create(submission_cap=1)
    assignment.due = yesterday
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
    # should fall back to submission cap before due date
    response = submit()
    assert response.status_code == 403, f"Expected status code 403, got {response}"


@login("student")
@pytest.mark.parametrize("due", (yesterday, tomorrow))
def test_submission_cap_with_override(client, assignment, student, due):
    """Test the submission cap with a per student override.

    The override should take place regardless of the due date of the :class:`.Assignment`.
    """
    assignment.due = due
    assignment.submission_caps.create(submission_cap=1, submission_cap_after_due=1)
    assignment.save()
    code = "print('hello, world')"
    assignment.save_grader_file(code)

    # add student override
    assignment.submission_caps.create(student=student, submission_cap=2, submission_cap_after_due=2)

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
def test_student_override_fallbacks_before(client, assignment, student):
    assignment.due = tomorrow
    assignment.submission_caps.create(submission_cap=1, submission_cap_after_due=2)
    assignment.save()
    assignment.save_grader_file("print('hello, world')")
    assignment.submission_caps.create(
        student=student, submission_cap=None, submission_cap_after_due=3
    )

    def submit():
        url = "assignments:submit"
        return client.post(
            reverse(url, args=[assignment.id]),
            {"text": "print('I hate fun')"},
        )

    response = submit()
    assert is_redirect(response), f"Expected redirect, got {response}"
    # should fall back to the assignment cap since the override is None
    response = submit()
    assert response.status_code == 403, f"Expected status code 403, got {response}"


@login("student")
def test_student_override_fallbacks_after(client, assignment, student):
    assignment.due = tomorrow
    assignment.submission_caps.create(submission_cap=1, submission_cap_after_due=1)
    assignment.save()
    assignment.save_grader_file("print('hello, world')")
    assignment.submission_caps.create(
        student=student, submission_cap=2, submission_cap_after_due=None
    )

    def submit():
        url = "assignments:submit"
        return client.post(
            reverse(url, args=[assignment.id]),
            {"text": "print('I hate fun')"},
        )

    response = submit()
    assert is_redirect(response), f"Expected redirect, got {response}"
    # should fall back to the normal student cap, not assignment cap
    # because for overdue it should fall back to the normal
    response = submit()
    assert is_redirect(response), f"Expected redirect, got {response}"
    # but now we've passed the cap for the student
    response = submit()
    assert response.status_code == 403, f"Expected status code 403, got {response}"


@login("student")
def test_submission_cap_on_quiz(client, quiz):
    quiz.submission_caps.create(submission_cap=1, submission_cap_after_due=1)
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


@login("teacher")
def test_create_student_override(client, assignment, student):
    client.post(
        reverse("assignments:student_submission", args=[assignment.id, student.id]),
        {"submission_cap": 2},
    )

    override = assignment.find_student_override(student)
    assert override is not None, "override should have been created"
    assert override.submission_cap == 2
