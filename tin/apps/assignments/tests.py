import pytest

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
@pytest.mark.parametrize("is_quiz", (-1, 0, 1, 2))
def test_create_assignment(client, course, is_quiz) -> None:
    data = {
        "name": "Write a Vertex Shader",
        "description": "See https://learnopengl.com/Getting-started/Shaders",
        "language": "P",
        "is_quiz": is_quiz,
        "filename": "vertex.glsl",
        "points_possible": "300",
        "due": "04/16/2025",
        "grader_timeout": "300",
        "submission_limit_count": "90",
        "submission_limit_interval": "30",
        "submission_limit_cooldown": "30",
    }
    response = client.post(
        reverse("assignments:add", args=[course.id]),
        data,
    )
    assert is_redirect(response)
    assignment_set = course.assignments.filter(name__exact=data["name"])
    assert assignment_set.count() == 1
    assignment = assignment_set.get()
    if is_quiz != -1:
        assert assignment.quiz.action == str(is_quiz)
    else:
        assert not hasattr(assignment, "quiz")
