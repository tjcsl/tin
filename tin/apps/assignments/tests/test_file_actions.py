from __future__ import annotations

import json

from django.urls import reverse

from tin.tests import login, model_to_dict

from ..models import FileAction


@login("teacher")
def test_choose_file_action_view(client, course, file_action) -> None:
    # make sure the view works
    response = client.get(reverse("assignments:choose_file_action", args=[course.id]))
    assert response.status_code == 200

    file_action.courses.clear()
    response = client.post(
        reverse("assignments:choose_file_action", args=[course.id]),
        {"file_action": file_action.id},
    )
    assert json.loads(response.content.decode("utf-8")).get("success") is True
    assert file_action.courses.filter(id=course.id).exists()


@login("teacher")
def test_create_file_action_view(client, course) -> None:
    url = reverse("assignments:create_file_action", args=[course.id])
    # make sure the view works normally
    response = client.get(url)
    assert response.status_code == 200

    response = client.post(url, {"name": "Hi", "command": "echo bye"})
    assert course.file_actions.count() == 1

    response = client.post(url, {"name": "Hi", "command": "echo $FILES"})
    assert (
        course.file_actions.count() == 1
    ), f"Creation form should error if $FILES is a command without a match value (got {response})"

    file_action = course.file_actions.first()
    assert file_action is not None
    fa_data = model_to_dict(file_action)

    # try copying the data
    response = client.post(f"{url}?action={file_action.id}", {**fa_data, "copy": True})
    assert (
        course.file_actions.count() == 2
    ), "Passing copy as a POST parameter should copy the file action"

    # or modifying the original instance
    client.post(f"{url}?action={file_action.id}", fa_data | {"name": "New name!"})
    file_action.refresh_from_db()
    assert file_action.name == "New name!"


@login("teacher")
def test_delete_file_action_view(client, course, file_action) -> None:
    response = client.post(
        f"{reverse('assignments:delete_file_action', args=[course.id])}",
        {"file_action": file_action.id},
    )
    assert json.loads(response.content.decode("utf-8")).get("success") is True

    # it should be removed from the course, but should still exist
    assert not course.file_actions.filter(id=file_action.id).exists()
    assert FileAction.objects.filter(id=file_action.id).exists()
