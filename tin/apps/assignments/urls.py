from django.urls import path

from . import views

app_name = "assignments"

urlpatterns = [
    path("<int:assignment_id>", views.show_view, name = "show"),
    path("<int:assignment_id>/students/<int:student_id>", views.student_submission_view, name = "student_submission"),
    path("add/course/<int:course_id>", views.create_view, name = "add"),
    path("<int:assignment_id>/edit", views.edit_view, name = "edit"),
    path("<int:assignment_id>/submit", views.submit_view, name = "submit"),
    path("<int:assignment_id>/scores_csv", views.scores_csv_view, name = "scores_csv"),
]
