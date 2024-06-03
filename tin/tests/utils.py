from __future__ import annotations

__all__ = ("login",)

from typing import TYPE_CHECKING, Any, Callable

import pytest

if TYPE_CHECKING:
    from typing_extensions import ParamSpec, TypeVar

    T = TypeVar("T", bound=object, default=None)
    P = ParamSpec("P")


def login(user: str, *args: Any) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Login ``client`` as a tin user type.

    .. code-block::

        @login("admin")
        def test_no_redirect(client, course):
            response = client.post(reverse("courses:index"), {})
            assert not_login_redirect(response)

        @login("teacher")
        def test_teacher_thing(client):
            # client is logged in as a teacher

        @login("student")
        def test_redirect(client):
            # client is a student

        def test_something(client):
            response = client.post(reverse("courses:index"), {})
            assert is_login_redirect(response)
    """
    return pytest.mark.usefixtures(f"{user}_login", *args)
