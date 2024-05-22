from django.urls import reverse

from ...tests.tin_test import TinTestCase
from .models import Course
from .views import index_view

COURSE_NAME = "Intro to OpenGL"


class TestCourseViews(TinTestCase):
    def setup(self) -> None:
        super().setup()
        self.course = self.create_course()

    def test_redirect(self) -> None:
        request = self.factory.get(reverse("courses:index"))
        request.user = self.anonymous
        response = index_view(request)

        assert response.status_code == 302
        assert response.url.startswith("/login/?next=")

    def test_create_course(self) -> None:
        COURSE_NAME = "Foundations of CS"
        response = self.client.post(
            reverse("courses:create"),
            {
                "name": [COURSE_NAME],
                "teacher": [f"{self.teacher.id}"],
                "sort_assignments_by": ["due_date"],
            },
        )
        assert response.status_code == 302
        assert Course.objects.filter(name__exact=COURSE_NAME).exists()

    def test_edit_course(self) -> None:
        response = self.client.post(
            reverse("courses:edit", args=[self.course.id]),
            {
                "name": [f"{COURSE_NAME} and Bezier Curves"],
                "teacher": [f"{self.teacher.id}"],
                "sort_assignments_by": ["due_date"],
            },
        )

        self.course.refresh_from_db()
        assert response.status_code == 302
        assert self.course.name == f"{COURSE_NAME} and Bezier Curves"

    def create_course(self, name: str = COURSE_NAME) -> Course:
        course, created = Course.objects.get_or_create(name=name)
        if created:
            course.teacher.add(self.teacher)
        return course
