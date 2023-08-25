from django.urls import path

from . import views

app_name = "assignments"

urlpatterns = [
    path("<int:assignment_id>", views.show_view, name="show"),
    path("add/course/<int:course_id>", views.create_view, name="add"),
    path("<int:assignment_id>/edit", views.edit_view, name="edit"),
    path("<int:assignment_id>/delete", views.delete_view, name="delete"),
    path("<int:assignment_id>/grader/upload", views.upload_grader_view, name="upload_grader"),
    path("<int:assignment_id>/files", views.manage_files_view, name="manage_files"),
    path(
        "<int:assignment_id>/files/delete/<int:file_id>",
        views.delete_file_view,
        name="delete_file",
    ),
    path(
        "<int:assignment_id>/files/compile_java_files",
        views.compile_java_files_view,
        name="compile_java_files",
    ),
    path(
        "<int:assignment_id>/students/<int:student_id>",
        views.student_submissions_view,
        name="student_submission",
    ),
    path("<int:assignment_id>/submit", views.submit_view, name="submit"),
    path("<int:assignment_id>/quiz", views.quiz_view, name="quiz"),
    path("<int:assignment_id>/report", views.quiz_report_view, name="report"),
    path("<int:assignment_id>/end", views.quiz_end_view, name="quiz_end"),
    path("<int:assignment_id>/clear/<int:user_id>", views.quiz_clear_view, name="clear"),
    path("<int:assignment_id>/scores_csv", views.scores_csv_view, name="scores_csv"),
    path(
        "<int:assignment_id>/download_submissions",
        views.download_submissions_view,
        name="download_submissions",
    ),
    path("<int:assignment_id>/download_log", views.download_log_view, name="download_log"),
    path("folder/<int:course_id>/<int:folder_id>", views.show_folder_view, name="show_folder"),
    path("add/folder/<int:course_id>", views.create_folder_view, name="add_folder"),
    path(
        "edit/folder/<int:course_id>/<int:folder_id>", views.edit_folder_view, name="edit_folder"
    ),
    path(
        "delete/folder/<int:course_id>/<int:folder_id>",
        views.delete_folder_view,
        name="delete_folder",
    ),
]
