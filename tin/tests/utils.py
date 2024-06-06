from __future__ import annotations

__all__ = (
    "login",
    "str_to_html",
    "to_html",
)

from typing import TYPE_CHECKING, Callable

import pytest
from django.template import Context, Engine

if TYPE_CHECKING:
    from typing_extensions import ParamSpec, TypeVar

    T = TypeVar("T", bound=object, default=None)
    P = ParamSpec("P")


def login(user: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
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
    return pytest.mark.usefixtures(f"{user}_login")


# we define these helper functions to avoid hardcoding
# stuff like the html escape code for '
def to_html(s: str, ctx: dict[str, str]):
    """Convert template code to an html string

    .. code-block:: pycon

        >>> template_logic = "Hello, my name is {{ username }}!"
        >>> context = {"username": "2027adeshpan"}
        >>> to_html(template_logic, context)
        'Hello, my name is 2027adeshpan!'

    Args:
        s: The template string (see :class:`~django.template.Template`)
        ctx: The variables/context to use for ``s`` (see :class:`~django.template.Context`)
    """
    template = Engine().from_string(s)
    context = Context(ctx)
    return template.render(context)


def str_to_html(s: str):
    """Converts a string to it's html representation

    .. code-block:: pycon

        >>> text = "It's annoying to remember HTML escape codes"
        >>> str_to_html(text)
        'It&#x27;s annoying to remember HTML escape codes'
    """
    template = "{{ var }}"
    ctx = {"var": s}
    return to_html(template, ctx)
