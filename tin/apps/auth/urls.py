from django.urls import path
from django.contrib.auth import views as django_auth_views

from . import views

app_name = "auth"

urlpatterns = [
    path("", views.index_view, name = "index"),
    path("login/", views.login_view, name = "login"),
    path("logout/", views.logout_view, name = "logout"),
    path("password-login/", django_auth_views.LoginView.as_view(template_name = "password-login.html"), name = "password_login"),
]
