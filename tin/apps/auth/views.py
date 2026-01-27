from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect, render

from ..courses.views import index_view as course_index_view


def index_view(request):
    """The startup page of Tin

    If the user is authenticated, redirects to the course index.
    Otherwise, the user has to log in

    Args:
        request: The request
    """
    if request.user.is_authenticated:
        return course_index_view(request)
    return login_view(request)


def login_view(request):
    """Login to Tin.

    If the user is authenticated, it will redirect to the course index.

    Args:
        request: The request
    """
    if request.user.is_authenticated:
        return course_index_view(request)
    return render(request, "login.html", {"debug": settings.DEBUG})


def logout_view(request):
    """Logout of Tin.

    .. note::

        This also resets the users access token.

    Args:
        request: The request
    """
    if request.user.is_authenticated:
        request.user.access_token = None
        request.user.save()
    logout(request)
    return redirect("auth:index")
