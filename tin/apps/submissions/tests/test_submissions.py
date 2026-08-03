import json
import os
from typing import TYPE_CHECKING

import psutil
import pytest
from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.urls import reverse
from django.utils import timezone

from tin.tests import is_redirect, login

from ..consumers import SubmissionJsonConsumer
from ..models import Comment

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser
    from django.test import Client

    from ...assignments.models import Assignment
    from ...courses.models import Course
    from ..models import Submission


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


@login("student")
def test_jsonapi_exists(client: Client, submission: Submission):
    response = client.get(reverse("submissions:show_json", args=[submission.id]))
    data = json.loads(response.content)
    assert isinstance(data, dict)

    # a nonexistent submission
    response = client.get(reverse("submissions:show_json", args=[1000000]))
    data = json.loads(response.content)
    assert data == {"error": "Submission not found"}


@login("student")
@pytest.mark.parametrize("language", ("P", "J"))
def test_download_submission(
    client: Client, assignment: Assignment, student: AbstractBaseUser, language: str
):
    extension = "py" if language == "P" else "java"
    assignment.filename = f"main.{extension}"
    assignment.save()

    submission = assignment.submissions.create(student=student)
    # Yes this isn't valid Java ;)
    code = "print('Hello World!')"
    submission.save_file(code)

    response = client.get(reverse("submissions:download", args=[submission.id]))

    assert (
        response["Content-Disposition"] == f'attachment; filename="{student.username}.{extension}"'
    )
    assert response.content.decode("utf-8") == submission.file_text_with_header


@login("teacher")
def test_comments(client: Client, teacher: AbstractBaseUser, submission: Submission):
    submission.complete = True
    submission.has_been_graded = True
    submission.save()

    # create comment
    response = client.post(
        reverse("submissions:comment", args=[submission.id]),
        {"comment": "HiABC", "point_override": "1.0"},
    )
    assert is_redirect(response)
    comments = submission.comments.filter(author=teacher).all()
    assert len(comments) == 1
    comment = comments[0]
    assert comment.text == "HiABC"

    # edit the comment
    response = client.post(
        reverse("submissions:edit_comment", args=[submission.id, comment.id]),
        {"text": "Hello", "point_override": "1.0"},
    )
    assert is_redirect(response)
    comment.refresh_from_db()
    assert comment.text == "Hello"

    # now delete it
    response = client.post(reverse("submissions:delete_comment", args=[submission.id, comment.id]))
    assert is_redirect(response)
    assert not submission.comments.filter(author=teacher).exists()


@login("teacher")
def test_public_comment(client: Client, submission: Submission):
    client.post(reverse("submissions:publish", args=[submission.id]))
    assert submission.published_submission is not None

    client.post(reverse("submissions:unpublish", args=[submission.id]))
    assert submission.published_submission is None


@login("admin")
@pytest.mark.skipif(
    psutil.pid_exists(2**22 + 1), reason="PID exists, so cannot check if it does not exist"
)
def test_set_aborted_complete_invalid_pid(client: Client, submission: Submission):
    submission.complete = False
    # on linux x64, 2^22 is the max PID so 2^22+1 should always not exist
    submission.grader_pid = 2**22 + 1
    submission.save()

    client.post(reverse("submissions:set_aborted_complete"))
    submission.refresh_from_db()
    assert submission.complete, "Should mark submission as complete if process has ended"


def test_set_aborted_complete_valid_pid(client: Client, submission: Submission):
    submission.complete = False
    submission.grader_pid = os.getpid()  # this PID exists
    submission.save()

    client.post(reverse("submissions:set_aborted_complete"))
    assert not submission.complete, "Should not mark submission as complete while running"


@login("admin")
def test_set_past_timeout_complete_view(
    client: Client, assignment: Assignment, submission: Submission
):
    assignment.enable_grader_timeout = True
    assignment.grader_timeout = 0
    assignment.save()
    submission.complete = False
    submission.grader_start_time = 0
    submission.save()

    client.post(reverse("submissions:set_past_timeout_complete"))
    submission.refresh_from_db()

    assert submission.complete

    submission.complete = False
    # the difference between the timestamp between now and when the timeout is called
    # should be close to 0, much less than the 1e12 grader timeout set
    submission.grader_start_time = timezone.localtime().timestamp()
    submission.save()
    assignment.grader_timeout = 1_000_000_000_000
    assignment.save()

    client.post(reverse("submissions:set_past_timeout_complete"))
    submission.refresh_from_db()

    assert not submission.complete


# --- CSRF: state-changing endpoints must be POST-only (a cross-site GET must not
# trigger them). POST behaviour is covered by test_public_comment / test_comments. ---


@login("teacher")
@pytest.mark.parametrize(
    "url_name", ("submissions:publish", "submissions:unpublish", "submissions:rerun")
)
def test_submission_action_rejects_get(client: Client, submission: Submission, url_name: str):
    assert client.get(reverse(url_name, args=[submission.id])).status_code == 405


@login("teacher")
def test_delete_comment_rejects_get(client: Client, submission: Submission, teacher):
    submission.complete = True
    submission.has_been_graded = True
    submission.save()
    comment = Comment.objects.create(
        submission=submission, author=teacher, start_char=0, end_char=1, text="x"
    )
    response = client.get(reverse("submissions:delete_comment", args=[submission.id, comment.id]))
    assert response.status_code == 405
    assert Comment.objects.filter(id=comment.id).exists()  # GET did nothing


# --- SubmissionJsonConsumer authorization: the live-update WebSocket must agree
# with the HTTP views (owner / course teacher / superuser only), not leak a
# classmate's submission (including quizzes). ---


@pytest.fixture
def in_memory_channels(settings):
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}


def _try_ws_connect(user, submission):
    """Drive the consumer directly with the scope the routing layer would supply."""

    async def scenario():
        communicator = WebsocketCommunicator(
            SubmissionJsonConsumer.as_asgi(), f"/submissions/{submission.id}.json"
        )
        communicator.scope["user"] = user
        communicator.scope["url_route"] = {"kwargs": {"submission_id": submission.id}}
        connected, _ = await communicator.connect()
        payload = await communicator.receive_json_from() if connected else None
        await communicator.disconnect()
        return connected, payload

    return async_to_sync(scenario)()


@pytest.mark.django_db(transaction=True)
def test_ws_owner_can_watch(in_memory_channels, submission, student):
    connected, payload = _try_ws_connect(student, submission)
    assert connected
    assert payload is not None


@pytest.mark.django_db(transaction=True)
def test_ws_teacher_can_watch(in_memory_channels, submission, teacher):
    connected, _ = _try_ws_connect(teacher, submission)
    assert connected


@pytest.mark.django_db(transaction=True)
def test_ws_classmate_cannot_watch(in_memory_channels, submission, course, django_user_model):
    classmate = django_user_model.objects.create(username="classmate", is_student=True)
    course.students.add(classmate)  # same course, not the owner
    connected, payload = _try_ws_connect(classmate, submission)
    assert not connected, f"classmate must be rejected; got {payload!r}"


@pytest.mark.django_db(transaction=True)
def test_ws_classmate_cannot_watch_quiz(
    in_memory_channels, quiz_submission, course, django_user_model
):
    classmate = django_user_model.objects.create(username="classmate2", is_student=True)
    course.students.add(classmate)
    connected, payload = _try_ws_connect(classmate, quiz_submission)
    assert not connected, f"classmate must not read a quiz submission; got {payload!r}"
