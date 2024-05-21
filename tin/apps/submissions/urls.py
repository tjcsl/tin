from __future__ import annotations

from django.urls import path

from . import views

app_name = "submissions"

urlpatterns = [
    path("<int:submission_id>", views.show_view, name="show"),
    path("<int:submission_id>.json", views.show_json_view, name="show_json"),
    path("<int:submission_id>/download", views.download_view, name="download"),
    path("<int:submission_id>/kill", views.kill_view, name="kill"),
    path("<int:submission_id>/rerun", views.rerun_view, name="rerun"),
    path("<int:submission_id>/comment", views.comment_view, name="comment"),
    path(
        "<int:submission_id>/comment/edit/<int:comment_id>",
        views.edit_comment_view,
        name="edit_comment",
    ),
    path(
        "<int:submission_id>/comment/delete/<int:comment_id>",
        views.delete_comment_view,
        name="delete_comment",
    ),
    path("<int:submission_id>/publish", views.publish_view, name="publish"),
    path("<int:submission_id>/unpublish", views.unpublish_view, name="unpublish"),
    path("filter", views.filter_view, name="filter"),
    path("set-aborted-complete", views.set_aborted_complete_view, name="set_aborted_complete"),
    path(
        "set-past-timeout-complete",
        views.set_past_timeout_complete_view,
        name="set_past_timeout_complete",
    ),
]
