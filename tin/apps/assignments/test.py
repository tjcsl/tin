from django.urls import reverse

from tin.apps.courses.models import Course
from tin.tests import TinTestCase


class AssignmentsTest(TinTestCase):
    usertype = "teacher"

    SAMPLE_ASSIGNMENT_DATA = {
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
    }

    def setup(self) -> None:
        super().setup()
        self.course, created = Course.objects.get_or_create(name="Intro to Vulkan")
        if created:
            self.course.teacher.add(self.teacher)

    def test_create_folder(self) -> None:
        response = self.client.post(
            reverse("assignments:add_folder", args=[self.course.id]), {"name": "Fragment Shader"}
        )
        assert response.status_code == 302
        assert self.course.folders.exists()

    def test_create_assignment(self) -> None:
        data = self.SAMPLE_ASSIGNMENT_DATA.copy()
        data["name"] += " 101"  # for identification purposes
        data["is_quiz"] = "-1"
        response = self.client.post(
            reverse("assignments:add", args=[self.course.id]),
            data,
        )
        assert response.status_code == 302
        assert self.course.assignments.filter(
            name__exact=self.SAMPLE_ASSIGNMENT_DATA["name"] + " 101"
        ).exists()

    def test_create_quiz(self) -> None:
        data = self.SAMPLE_ASSIGNMENT_DATA.copy()
        data["is_quiz"] = "2"
        response = self.client.post(
            reverse("assignments:add", args=[self.course.id]),
            data,
        )
        assert response.status_code == 302
        assignment_set = self.course.assignments.filter(
            name__exact=self.SAMPLE_ASSIGNMENT_DATA["name"]
        )
        assert assignment_set.count() == 1
        assignment = assignment_set.get()
        assert assignment.quiz.action == "2"
