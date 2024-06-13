from __future__ import annotations

import pytest
from django.utils import timezone

import tin.tests.create_users as users
from tin.apps.courses.models import Course

PASSWORD = "Made with <3 by 2027adeshpan"


@pytest.fixture(autouse=True)
def create_users():
    users.add_users_to_database(password=PASSWORD, verbose=False)


@pytest.fixture
def admin(django_user_model):
    """Fixture to pass in an Admin user into a test

    .. code-block:: python

        def test_admin_user(admin):
            assert admin.is_superuser
    """
    return django_user_model.objects.get(username="admin")


@pytest.fixture
def teacher(django_user_model):
    """Fixture to pass in a Teacher user into a test

    .. code-block:: python

        def test_create_assignment(teacher):
            # create assignment using a teacher User
    """
    return django_user_model.objects.get(username="teacher")


@pytest.fixture
def student(django_user_model):
    """Fixture to pass in a Student user into a test

    .. code-block:: python

        def test_student_sees_assignment(student):
            # check if student user can see assignment
    """
    return django_user_model.objects.get(username="student")


@pytest.fixture
def course(teacher, student):
    """Fixture containing a course object

    The name of the course is "Intro to OpenGL",
    and the teacher is the same teacher as given by
    :func:`~.teacher` and a student is from :func:`~.student`
    """
    course = Course.objects.create(name="Intro to OpenGL")
    course.teacher.add(teacher)
    course.students.add(student)
    return course


@pytest.fixture
def assignment(course):
    """Creates an assignment in :func:`~.course`"""
    data = {
        "name": "Write a Shader",
        "description": "See https://learnopengl.com/Getting-started/Shaders",
        "points_possible": "300",
        "due": timezone.now(),
    }
    return course.assignments.create(**data)


@pytest.fixture
def quiz(assignment):
    """Creates a quiz in :func:`~.course`"""
    assignment.is_quiz = True
    assignment.save()
    return assignment


@pytest.fixture
def submission(assignment, student):
    """Creates a :class:`.Submission`.

    The submission is for :func:`assignment` and was submitted
    by :func:`student`. The submission text is ``print('Hello World!')``.
    """
    submission = assignment.submissions.create(student=student)
    submission.save_file("print('Hello World!')")
    return submission


@pytest.fixture
def quiz_submission(quiz, student):
    """Creates a :class:`.Submission`.

    The submission is for :func:`quiz` and was submitted
    by :func:`student`. The submission text is ``print('Hello World!')``.
    """
    submission = quiz.submissions.create(student=student)
    submission.save_file("print('Hello World!')")
    return submission


@pytest.fixture
def admin_login(client):
    """Convenience fixture for logging in as admin.

    Use the decorator :func:`.login` to save writing

    .. code-block:: python

        @login("admin")
        def test_redirect(client, course):
            response = client.get(reverse("assignments:edit", args=[course.id]))
            assert response.status_code != 302
    """
    client.login(username="admin", password=PASSWORD)


@pytest.fixture
def teacher_login(client):
    """Convenience fixture for logging in as a teacher

    Use the decorator :func:`.login` to save writing

    .. code-block:: python

        @login("teacher")
        def test_redirect(client, course):
            response = client.get(reverse("assignments:edit", args=[course.id]))
            assert response.status_code != 302
    """
    client.login(username="teacher", password=PASSWORD)


@pytest.fixture
def student_login(client):
    """Convenience decorator for logging in as a teacher

    Use the decorator :func:`.login` to save writing

    .. code-block:: python

        @login("student")
        def test_redirect(client, course):
            response = client.get(reverse("assignments:edit", args=[course.id]))
            assert response.status_code == 302
    """
    client.login(username="student", password=PASSWORD)
