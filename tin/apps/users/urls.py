from __future__ import annotations

from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("theme/", views.change_theme, name="theme"),
]
