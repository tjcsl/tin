from django.urls import path

from . import views

app_name = "assignments"

urlpatterns = [
    path("<int:assignment_id>", views.show_view, name="show"),
    path(
        "<int:assignment_id>/students/<int:student_id>",
        views.student_submission_view,
        name="student_submission",
    ),
    path("add/course/<int:course_id>", views.create_view, name="add"),
    path("<int:assignment_id>/edit", views.edit_view, name="edit"),
    path("<int:assignment_id>/delete", views.delete_view, name="delete"),
    path("<int:assignment_id>/grader/upload", views.upload_grader_view, name="upload_grader"),
    path("<int:assignment_id>/submit", views.submit_view, name="submit"),
    path("<int:assignment_id>/scores_csv", views.scores_csv_view, name="scores_csv"),
    path(
        "<int:assignment_id>/download_submissions",
        views.download_submissions_view,
        name="download_submissions",
    ),
    path("<int:assignment_id>/download_log", views.download_log_view, name="download_log"),
    path("add/folder/<int:course_id>", views.create_folder_view, name="add_folder"),
    path(
        "remove/folder/<int:course_id>/<int:folder_id>",
        views.remove_folder_view,
        name="remove_folder",
    ),
    path("folder/<int:course_id>/<int:folder_id>", views.show_folder_view, name="show_folder"),
    path("upload", views.upload, name="upload_file"),
]
