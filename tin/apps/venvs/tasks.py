from celery import shared_task

from ..assignments.models import Assignment
from .models import Virtualenv, VirtualenvCreationError


@shared_task
def create_virtualenv(assignment_id):
    assignment = Assignment.objects.get(id=assignment_id)

    if assignment.venv_object_created:
        return

    try:
        Virtualenv.create_venv_for_assignment(assignment)
    except VirtualenvCreationError:
        pass


@shared_task
def install_packages(venv_id, package_names):
    venv = Virtualenv.objects.get(id=venv_id)

    venv.install_packages(package_names)
