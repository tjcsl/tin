from __future__ import annotations

from django.conf import settings


def response_footer(_request):
    return {
        "DEVELOPER_EMAIL": settings.DEVELOPER_EMAIL,
        "REPO_URL": settings.REPO_URL,
    }

def dark_mode(request):
    return {
        'dark_mode_enabled': getattr(request.user, 'dark_mode', False)
    }