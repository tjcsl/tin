from django import http
from django.shortcuts import get_object_or_404, redirect, render

from ..assignments.models import Language
from ..auth.decorators import teacher_or_superuser_required
from .forms import VenvForm
from .models import Venv
from .tasks import create_venv, install_packages


# Create your views here.
@teacher_or_superuser_required
def index_view(request):
    """Show all venvs visible to a user

    Args:
        request: The request
    """
    venvs = Venv.objects.filter_visible(request.user)

    return render(
        request,
        "venvs/index.html",
        {
            "venvs_app": True,
            "venvs": venvs,
        },
    )


@teacher_or_superuser_required
def show_view(request, venv_id):
    """Show information about a venv

    Args:
        request: The request
        venv_id: The primary key of an instance of the :class:`.Venv` model
    """
    venv: Venv = get_object_or_404(Venv.objects.filter_visible(request.user), id=venv_id)

    return render(
        request,
        "venvs/show.html",
        {
            "venvs_app": True,
            "nav_item": venv.name,
            "venv": venv,
        },
    )


@teacher_or_superuser_required
def create_view(request):
    """Create a venv

    Args:
        request: The request
    """
    if request.method == "POST":
        form = VenvForm(request.POST)
        if form.is_valid():
            venv = form.save(commit=False)
            venv.fully_created = False
            venv.save()
            create_venv.delay(venv.id)
            return redirect("venvs:show", venv.id)
    else:
        form = VenvForm(initial={"language": Language.objects.filter(language="P").first()})
    return render(
        request,
        "venvs/edit_create.html",
        {
            "venvs_app": True,
            "nav_item": "Create virtual environment",
            "form": form,
        },
    )


@teacher_or_superuser_required
def edit_view(request, venv_id):
    """Edit a venv

    Args:
        request: The request
        venv_id: The primary key of an instance of the :class:`.Venv` model
    """
    venv = get_object_or_404(Venv.objects.filter_editable(request.user), id=venv_id)

    if request.method == "POST":
        form = VenvForm(data=request.POST, instance=venv)
        if form.is_valid():
            venv = form.save()
            return redirect("venvs:show", venv.id)
    else:
        form = VenvForm(instance=venv)

    return render(
        request,
        "courses/edit_create.html",
        {
            "venvs_app": True,
            "nav_item": "Edit",
            "venv": venv,
            "form": form,
        },
    )


@teacher_or_superuser_required
def install_packages_view(request, venv_id):
    """Install packages in a venv

    Args:
        request: The request
        venv_id: The primary key of an instance of the :class:`.Venv` model
    """
    if request.method == "POST":
        venv = get_object_or_404(
            Venv.objects.filter_editable(request.user), id=venv_id, installing_packages=False
        )

        venv.installing_packages = True
        venv.save()

        packages = list(filter(bool, request.POST.getlist("packages[]")))

        install_packages.delay(venv.id, packages)

        return redirect("venvs:show", venv.id)

    raise http.Http404
