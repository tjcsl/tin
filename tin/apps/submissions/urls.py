from django.urls import path

from . import views

app_name = "submissions"

urlpatterns = [
    path("<int:submission_id>", views.show_view, name = "show"),
    path("<int:submission_id>.json", views.show_json_view, name = "show_json"),
]
