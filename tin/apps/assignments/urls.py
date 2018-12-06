from django.urls import path

from . import views

app_name = "assignments"

urlpatterns = [
    path("<int:assignment_id>", views.show_view, name = "show"),
    path("<int:assignment_id>/students/<int:student_id>", views.student_submission_view, name = "student_submission"),
]
