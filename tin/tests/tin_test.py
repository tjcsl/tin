from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

import tin.tests.create_users as users

PASSWORD = "Made with <3 by 2027adeshpan"
User = get_user_model()


class TinTestCase(TestCase):
    """
    A convenience class for common Tin operations in tests,
    like making users, admins, and staff.

    The default client login is as admin, but can be changed
    via the ``usertype`` class attribute.

    Different types of users are already created for ease
    of use, and can be accessed as self.admin, self.teacher,
    self.student, and self.anonymous

    Examples
    --------

    .. code-block:: python

        class MyStudentTest(TinTestCase):
            # now self.client is a student
            usertype = "student"


        class MyStaffTest(TinTestCase):
            # now self.client is a teacher member only
            usertype = "teacher"


        class MyNonLoggedInTest(TinTestCase):
            # self.client will not be logged in
            usertype = None

    """

    usertype: str = "admin"
    """
    Whether logged in user is an admin, teacher, or student.
    Should be ``None`` if unused
    """

    def setUp(self) -> None:
        super().setUp()
        self.setup()

    def setup(self) -> None:
        users.add_users_to_database(password=PASSWORD, debug=False)

        # in theory you could do this in a loop with setattr
        # but autocomplete is nice so we hardcode
        self.admin = User.objects.get(username="admin")
        self.teacher = User.objects.get(username="teacher")
        self.student = User.objects.get(username="student")
        self.anonymous = AnonymousUser()

        self.factory = RequestFactory()

        if self.usertype is None:
            return

        if self.usertype not in {user[0] for user in users.user_data}:
            raise ValueError("Could not figure out type of logged in user")
        self.login(self.usertype)

    def login(self, username: str) -> User:
        """Logs in the client by username"""
        self.client.login(username=username, password=PASSWORD)
