from __future__ import annotations

from django.shortcuts import render


def handle_404_view(request, exception):
    """A 404 view

    Args:
        request: The request
        exception: The exception (if any) that caused this view
    """
    return render(request, "error/404.html", status=404)


def handle_500_view(request):
    """Internal server error

    Args:
        request: The request
    """
    return render(request, "error/500.html", status=500)
