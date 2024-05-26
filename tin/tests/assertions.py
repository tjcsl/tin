"""
A module containing frequently used
checks throughout the tests
"""

from __future__ import annotations

from typing import Literal

from django.http import HttpResponse, HttpResponseRedirect

__all__ = (
    "is_redirect",
    "not_redirect",
    "is_login_redirect",
    "not_login_redirect",
)


def is_redirect(
    response: HttpResponse, url: str | None = None, part: Literal["base", "full", "end"] = "full"
) -> bool:
    """
    Checks if ``response`` is a redirect.

    Parameters
    ----------
        url
            Checks if redirect url is the same as url

        part
            Which part of the url to check. Can be base, full, or end.
    """
    if not (isinstance(response, HttpResponseRedirect) and response.status_code == 302):
        return False

    if url is None:
        return True

    if part == "base":
        return response.url.startswith(url)
    if part == "full":
        return response.url == url
    return part.endswith(url)


def not_redirect(response: HttpResponse) -> bool:
    """
    Inverse of :meth:`is_redirect`
    """
    return not is_redirect(response)


def is_login_redirect(response: HttpResponse, next: str | None = None) -> bool:
    """Checks if a response is a redirect to a login page

    If the parameter ``next`` is passed, checks if the success_url
    of the login is that url
    """
    login_success_url = "/login/"
    if next is not None and isinstance(next, str):
        login_success_url += f"?next={next}"

    return is_redirect(response, url=login_success_url, part="base")


def not_login_redirect(response: HttpResponse, **kwargs: str | None) -> bool:
    """Inverse of :meth:`is_login_redirect`"""
    return not is_login_redirect(response, **kwargs)
