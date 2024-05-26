from __future__ import annotations

__all__ = ("admin", "teacher", "student")

from typing import TYPE_CHECKING, Any, Callable, overload

import pytest

if TYPE_CHECKING:
    from typing_extensions import ParamSpec, TypeVar

    T = TypeVar("T", bound=object, default=None)
    P = ParamSpec("P")

    TestFunction = Callable[..., object]
    TestFunctionDecorator = Callable[[TestFunction], TestFunction]


# we need this function to take into account usage as
# @admin() or @admin
@overload
def apply_fixture(__f: Callable[P, T], prefix: str, **kwargs: Any) -> Callable[P, T]: ...


@overload
def apply_fixture(__f: None, prefix: str, **kwargs: Any) -> TestFunctionDecorator: ...


def apply_fixture(__f: TestFunction | None, /, prefix: str, **kwargs: Any):
    fixture = pytest.mark.usefixtures(prefix, **kwargs)
    if __f is not None and callable(__f):
        return fixture(__f)
    return fixture


@overload
def admin(__f: TestFunction, /, **kwargs: Any) -> TestFunction: ...


@overload
def admin(__f: None, /, **kwargs: Any) -> TestFunctionDecorator: ...


def admin(__f: TestFunction | None = None, /, **kwargs: Any):
    """
    Log in as an admin.

    .. code-block:: python

        @admin
        def test_something(client):
            # client is logged in as an admin


        @admin(kwarg_for_usefixtures=xyz)
        def test_something(client):
            # client is logged in as an admin
    """
    return apply_fixture(__f, "admin_login", **kwargs)


@overload
def teacher(__f: TestFunction, /, **kwargs: Any) -> TestFunction: ...


@overload
def teacher(__f: None, /, **kwargs: Any) -> TestFunctionDecorator: ...


def teacher(__f: TestFunction | None = None, /, **kwargs: Any):
    """
    Log in as a teacher

    .. code-block:: python

        @teacher
        def test_something(client):
            # client is logged in as a teacher


        @teacher(kwarg_for_usefixtures=xyz)
        def test_something(client):
            # client is logged in as a teacher
    """
    return apply_fixture(__f, "teacher_login", **kwargs)


@overload
def student(__f: TestFunction, /, **kwargs: Any) -> TestFunction: ...


@overload
def student(__f: None, /, **kwargs: Any) -> TestFunctionDecorator: ...


def student(__f: TestFunction | None = None, /, **kwargs: Any):
    """
    Log in as a student

    .. code-block:: python

        @student
        def test_something(client):
            # client is logged in as a student


        @student(kwarg_for_usefixtures=xyz)
        def test_something(client):
            # client is logged in as a student
    """
    return apply_fixture(__f, "student_login", **kwargs)
