from django.conf import settings


def response_footer(_request):
    return {
        "DEVELOPER_EMAIL": settings.DEVELOPER_EMAIL,
        "REPO_URL": settings.REPO_URL,
    }
