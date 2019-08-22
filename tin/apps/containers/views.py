from django import http
from django.shortcuts import redirect, render

from ..auth.decorators import superuser_required
from ..containers.tasks import periodic_container_checks


@superuser_required
def periodic_checks_view(request):
    if request.method == "POST" and request.POST["confirm"] == "CONFIRM":
        periodic_container_checks.delay()

        return redirect("auth:index")

    return render(request, "containers/run-periodic-checks.html", {"nav_item": "Periodic container checks"})

