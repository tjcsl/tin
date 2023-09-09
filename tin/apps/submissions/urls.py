from django.urls import path

from . import views

app_name = "submissions"

urlpatterns = [
    path("<int:submission_id>", views.show_view, name="show"),
    path("<int:submission_id>.json", views.show_json_view, name="show_json"),
    path("<int:submission_id>/kill", views.kill_view, name="kill"),
    path("<int:submission_id>/rerun", views.rerun_view, name="rerun"),
    path("<int:submission_id>/comment", views.comment_view, name="comment"),
    path("set-aborted-complete", views.set_aborted_complete_view, name="set_aborted_complete"),
    path(
        "set-past-timeout-complete",
        views.set_past_timeout_complete_view,
        name="set_past_timeout_complete",
    ),
]
