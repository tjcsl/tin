"""
A module containing frequently used
checks throughout the tests
"""

from __future__ import annotations

from django.http import HttpResponse, HttpResponseRedirect

__all__ = (
    "is_redirect",
    "not_redirect",
    "is_login_redirect",
    "not_login_redirect",
)


def is_redirect(response: HttpResponse) -> bool:
    return isinstance(response, HttpResponseRedirect) and response.status_code == 302


def not_redirect(response: HttpResponse) -> bool:
    return not is_redirect(response)


def is_login_redirect(response: HttpResponse, next: str | None = None) -> bool:
    """Checks if a response is a redirect to a login page

    If the parameter ``next`` is passed, checks if the success_url
    of the login is that url
    """
    login_success_url = "/login/"
    if next is not None and isinstance(next, str):
        login_success_url += f"?next={next}"

    return (
        # typecheckers don't realize is_redirect already makes sure
        # it is an HttpResponseRedirect, so we have to duplicate
        # that function here
        isinstance(response, HttpResponseRedirect)
        and response.status_code == 302
        and response.url.startswith(login_success_url)
    )


def not_login_redirect(response: HttpResponse, **kwargs: str | None) -> bool:
    """Inverse of :meth:`is_login_redirect`"""
    return not is_login_redirect(response, **kwargs)
