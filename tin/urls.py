"""tin URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from tin.apps.errors.views import (handle_404_view, handle_500_view)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('social_django.urls', namespace='social')),

    path('courses/', include("tin.apps.courses.urls", namespace="courses")),
    path('assignments/', include("tin.apps.assignments.urls", namespace="assignments")),
    path('submissions/', include("tin.apps.submissions.urls", namespace="submissions")),

    path('users/', include("tin.apps.users.urls", namespace="users")),
    path('', include("tin.apps.auth.urls", namespace="auth")),
]

handler404 = handle_404_view
handler500 = handle_500_view
