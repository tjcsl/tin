from django import http
from django.shortcuts import redirect

from ..auth.decorators import superuser_required
from ..containers.tasks import periodic_container_checks


@superuser_required
def periodic_checks_view(request):
    if request.method != "POST":
        raise http.Http404

    periodic_container_checks.delay()

    return redirect("auth:index")

