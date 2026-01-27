import io

from django.conf import settings
from django.urls import reverse

from tin.tests import is_redirect, login, str_to_html


@login("teacher")
def test_create_folder(client, course) -> None:
    response = client.post(
        reverse("assignments:add_folder", args=[course.id]), {"name": "Fragment Shader"}
    )
    assert is_redirect(response)
    assert course.folders.exists()


@login("teacher")
def test_delete_folder(client, course) -> None:
    folder = course.folders.create(name="My Folder")
    response = client.post(reverse("assignments:delete_folder", args=[course.id, folder.id]))

    assert is_redirect(response)
    assert not course.folders.exists()


@login("teacher")
def test_incorrect_files(client, assignment):
    binary_data = io.BytesIO(b"b" * (settings.SUBMISSION_SIZE_LIMIT + 1))
    response = client.post(
        reverse("assignments:manage_files", args=[assignment.id]), {"upload_file": binary_data}
    )

    error = str_to_html("That file's too large.")
    assert error in response.content.decode("utf-8")


@login("teacher")
def test_files_management(client, assignment):
    sample_grader = io.BytesIO(b"some text")
    response = client.post(
        reverse("assignments:manage_files", args=[assignment.id]), {"upload_file": sample_grader}
    )

    assert is_redirect(response)
