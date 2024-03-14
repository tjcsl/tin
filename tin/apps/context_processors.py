from django.conf import settings


def response_footer(request):  # pylint:disable=unused-argument
    return {
        "DEVELOPER_EMAIL": settings.DEVELOPER_EMAIL,
        "REPO_URL": settings.REPO_URL,
    }
