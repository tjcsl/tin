from __future__ import annotations

from django import http
from django.contrib.auth.decorators import login_required

from tin.apps.users.forms import ThemeForm


@login_required
def change_theme(request):
    """Sets the color theme"""
    if request.method == "POST":
        form = ThemeForm(request.POST)
        if form.is_valid():
            request.user.dark_mode = form.cleaned_data["dark_mode"]
            request.user.save()
            return http.JsonResponse({"success": True})
        else:
            return http.JsonResponse({"success": False, "errors": form.errors.as_json()}, status=400)
    raise http.Http404
