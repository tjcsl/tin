from django.urls import path

from . import views

app_name = "courses"

urlpatterns = [
    path("", views.index_view, name = "index"),
    path("new/", views.create_view, name = "create"),
    path("<int:course_id>", views.show_view, name = "show"),
]
