from django.http import HttpResponse
from django.contrib.auth import logout
from django.shortcuts import render, redirect

from ..courses.views import index_view as course_index_view

def index_view(request):
    if request.user.is_authenticated:
        return course_index_view(request)
    else:
        return login_view(request)


def login_view(request):
    return render(request, "login.html")


def logout_view(request):
    if request.user.is_authenticated:
        request.user.access_token = None
        request.user.save()
    logout(request)
    return redirect("auth:index")
