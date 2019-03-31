from django.conf import settings

def response_developer_email(request):
    return {"DEVELOPER_EMAIL": settings.DEVELOPER_EMAIL}
