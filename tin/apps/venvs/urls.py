from __future__ import annotations

from django.urls import path

from . import views

app_name = "venvs"

urlpatterns = [
    path("", views.index_view, name="index"),
    path("<int:venv_id>", views.show_view, name="show"),
    path("add", views.create_view, name="add"),
    path("<int:venv_id>/install_packages", views.install_packages_view, name="install_packages"),
]
