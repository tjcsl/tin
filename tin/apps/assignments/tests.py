from __future__ import annotations

from django.urls import reverse

from tin.tests import is_redirect, teacher


@teacher
def test_create_folder(client, course) -> None:
    response = client.post(
        reverse("assignments:add_folder", args=[course.id]), {"name": "Fragment Shader"}
    )
    assert is_redirect(response)
    assert course.folders.exists()


@teacher
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
    }
    response = client.post(
        reverse("assignments:add", args=[course.id]),
        data,
    )
    assert is_redirect(response)
    assignment_set = course.assignments.filter(name__exact=data["name"])
    assert assignment_set.count() == 1
