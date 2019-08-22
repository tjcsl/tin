from django.urls import path

from . import views

app_name = "containers"

urlpatterns = [path("run-periodic-checks", views.periodic_checks_view, name="run_periodic_checks")]
