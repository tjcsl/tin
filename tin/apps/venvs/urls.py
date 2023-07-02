from django.urls import path

from . import views

app_name = "venvs"

urlpatterns = [
    path("<int:venv_id>", views.show_view, name="show"),
    path(
        "create-for-assignment/<int:assignment_id>",
        views.create_for_assignment_view,
        name="create-for-assignment",
    ),
    path("<int:venv_id>/install-packages", views.install_view, name="install-packages"),
]
