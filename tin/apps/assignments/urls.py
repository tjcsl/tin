from django.urls import path

from . import views

app_name = "assignments"

urlpatterns = [
    path("<int:assignment_id>", views.show_view, name = "show"),
]
