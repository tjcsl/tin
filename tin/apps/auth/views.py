from __future__ import annotations

from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect, render

from ..courses.views import index_view as course_index_view


def index_view(request):
    if request.user.is_authenticated:
        return course_index_view(request)
    return login_view(request)


def login_view(request):
    if request.user.is_authenticated:
        return course_index_view(request)
    return render(request, "login.html", {"debug": settings.DEBUG})


def logout_view(request):
    if request.user.is_authenticated:
        request.user.access_token = None
        request.user.save()
    logout(request)
    return redirect("auth:index")
