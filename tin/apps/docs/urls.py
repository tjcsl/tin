from django.urls import path

from . import views

app_name = "docs"

urlpatterns = [
    path("", views.index_view, name = "index"),
    path("graders", views.graders_view, name = "graders"),
    path("sample-graders", views.sample_graders_view, name = "sample-graders"),
]

