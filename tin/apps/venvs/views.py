from django import http
from django.shortcuts import get_object_or_404, redirect, render

from ..assignments.models import Assignment
from ..auth.decorators import teacher_or_superuser_required
from .models import Virtualenv
from .tasks import create_virtualenv, install_packages

# Create your views here.


@teacher_or_superuser_required
def show_view(request, venv_id):
    venv = get_object_or_404(Virtualenv, id=venv_id)
    if request.user != venv.assignment.course.teacher and not request.user.is_superuser:
        raise http.Http404

    return render(
        request,
        "venvs/show.html",
        {
            "course": venv.assignment.course,
            "assignment": venv.assignment,
            "nav_item": "Virtual environment",
            "venv": venv,
        },
    )


@teacher_or_superuser_required
def install_view(request, venv_id):
    if request.method == "POST":
        venv = get_object_or_404(Virtualenv, id=venv_id)
        if request.user != venv.assignment.course.teacher and not request.user.is_superuser:
            raise http.Http404

        venv.installing_packages = True
        venv.save()

        packages = list(filter(bool, request.POST.getlist("packages[]")))

        install_packages.delay(venv.id, packages)

        return redirect("venvs:show", venv.id)

    raise http.Http404


@teacher_or_superuser_required
def create_for_assignment_view(request, assignment_id):
    if request.method == "POST":
        assignment = get_object_or_404(Assignment, id=assignment_id)
        if request.user != assignment.course.teacher and not request.user.is_superuser:
            raise http.Http404

        create_virtualenv.delay(assignment.id)

        return redirect("assignments:show", assignment.id)

    raise http.Http404
