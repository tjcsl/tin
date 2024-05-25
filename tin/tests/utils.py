from __future__ import annotations

__all__ = ("admin", "teacher", "student")

from typing import Callable

import pytest


# we need this function to take into account usage as
# @admin() or @admin
def apply_fixture(__f: Callable[..., object] | None, /, prefix: str, **kwargs):
    fixture = pytest.mark.usefixtures(f"{prefix}_login", **kwargs)
    if __f is not None and callable(__f):
        return fixture(__f)
    return fixture


def admin(__f: Callable[..., object] | None = None, /, **kwargs):
    """
    Log in as an admin.

    .. code-block:: python

        @admin
        def test_something(client):
            # client is logged in as an admin


        @admin(kwargs_for_usefixtures=xyz)
        def test_something(client):
            # client is logged in as an admin
    """
    return apply_fixture(__f, "admin", **kwargs)


def teacher(__f: Callable[..., object] | None = None, /, **kwargs):
    """
    Log in as a teacher

    .. code-block:: python

        @teacher
        def test_something(client):
            # client is logged in as a teacher


        @teacher(kwargs_for_usefixtures=xyz)
        def test_something(client):
            # client is logged in as a teacher
    """
    return apply_fixture(__f, "teacher", **kwargs)


def student(__f: Callable[..., object] | None = None, /, **kwargs):
    """
    Log in as a student

    .. code-block:: python

        @student
        def test_something(client):
            # client is logged in as a student


        @student(kwargs_for_usefixtures=xyz)
        def test_something(client):
            # client is logged in as a student
    """
    return apply_fixture(__f, "student", **kwargs)
