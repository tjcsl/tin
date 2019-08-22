from django.conf import settings


def response_developer_email(request):  # pylint:disable=unused-argument
    return {"DEVELOPER_EMAIL": settings.DEVELOPER_EMAIL}
