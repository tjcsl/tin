from django.urls import reverse

from tin.tests import teacher

from .models import Course


@teacher
def test_create_course(client, teacher) -> None:
    COURSE_NAME = "Foundations of CS"
    response = client.post(
        reverse("courses:create"),
        {
            "name": [COURSE_NAME],
            "teacher": [f"{teacher.id}"],
            "sort_assignments_by": ["due_date"],
        },
    )
    assert response.status_code == 302
    filter_ = Course.objects.filter(name__exact=COURSE_NAME)
    assert filter_.count() == 1
    course = filter_.get()
    assert course.name == COURSE_NAME


@teacher
def test_edit_course(client, course, teacher) -> None:
    old_name = course.name
    response = client.post(
        reverse("courses:edit", args=[course.id]),
        {
            "name": [f"{old_name} and Bezier Curves"],
            "teacher": [f"{teacher.id}"],
            "sort_assignments_by": ["due_date"],
        },
    )

    course.refresh_from_db()
    assert response.status_code == 302
    assert course.name == f"{old_name} and Bezier Curves"


def test_redirect(client) -> None:
    response = client.get(reverse("courses:index"))

    assert response.status_code == 302
    assert response.url.startswith("/login/?next=")
