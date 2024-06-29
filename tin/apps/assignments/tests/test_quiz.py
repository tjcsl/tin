from __future__ import annotations

import json

import pytest
from django.conf import settings
from django.urls import reverse

from tin.tests import is_redirect, login


@login("student")
def test_submit_quiz_as_assignment(client, quiz):
    response = client.post(
        reverse("assignments:submit", args=[quiz.id]), {"text": "print('I hate CSS')"}
    )

    assert response.status_code == 404


@login("student")
def test_submit_quiz(client, quiz):
    response = client.post(
        reverse("assignments:quiz", args=[quiz.id]), {"text": "print('I hate CSS')"}
    )

    assert is_redirect(response)
    assert quiz.submissions.count() == 1


@login("student")
def test_submit_assigment_as_quiz(client, assignment):
    response = client.post(
        reverse("assignments:quiz", args=[assignment.id]), {"text": "print('I hate CSS')"}
    )

    assert response.status_code == 404


@login("student")
def test_quiz_ended_has_message(client, quiz):
    response = client.post(reverse("assignments:quiz_end", args=[quiz.id]))
    assert is_redirect(response)
    all = tuple(msg for msg in quiz.log_messages.all())
    assert len(all) == 1
    (first,) = all
    assert first.content == "Ended quiz"

    response = client.post(
        reverse("assignments:quiz", args=[quiz.id]), {"text": "print('I hate CSS')"}
    )

    assert response.status_code == 404


@login("student")
def test_quiz_data_basic(client, quiz):
    response = client.get(reverse("assignments:report", args=[quiz.id]))
    data = json.loads(response.content.decode("utf-8"))
    assert data == {"action": "no action"}


@login("teacher")
@pytest.mark.parametrize(
    ("quiz_action", "action"),
    (("1", "color"), ("2", "lock")),
)
def test_quiz_data_with_severity(client, quiz, quiz_action, action):
    quiz.quiz_action = quiz_action
    quiz.save()

    response = client.get(
        reverse("assignments:report", args=[quiz.id]),
        {"severity": settings.QUIZ_ISSUE_THRESHOLD, "content": "hi"},
    )
    data = json.loads(response.content.decode("utf-8"))
    assert data == {"action": action}

    msgs = tuple(quiz.log_messages.all())
    assert len(msgs) == 1
    assert msgs[0].content == "hi"


@login("teacher")
def test_quiz_data_after_close(client, quiz):
    # this should end the quiz
    client.post(reverse("assignments:quiz_end", args=[quiz.id]))
    response = client.get(
        reverse("assignments:report", args=[quiz.id]),
        {"severity": settings.QUIZ_ISSUE_THRESHOLD, "content": "hi"},
    )

    assert json.loads(response.content.decode("utf-8")) == {"action": "no action"}
    msgs = tuple(quiz.log_messages.all())
    assert len(msgs) == 1
    assert msgs[0].content == "Ended quiz"


@login("teacher")
def test_clear_quiz_messages(client, student, quiz):
    quiz.log_messages.create(student=student, content="hi", severity=0)
    response = client.post(reverse("assignments:clear", args=[quiz.id, student.id]))
    assert is_redirect(response)
    assert not quiz.log_messages.exists()
