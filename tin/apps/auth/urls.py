from __future__ import annotations

from django.conf import settings
from django.contrib.auth import views as django_auth_views
from django.urls import path

from . import views

app_name = "auth"

urlpatterns = [
    path("", views.index_view, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]
if settings.DEBUG:
    urlpatterns.append(
        path(
            "password-login/",
            django_auth_views.LoginView.as_view(template_name="password-login.html"),
            name="password_login",
        )
    )
