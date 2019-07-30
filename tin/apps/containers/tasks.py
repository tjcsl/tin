from contextlib import contextmanager

from celery import shared_task
from django.db import models
from django.db import IntegrityError
from django.conf import settings
from django.utils import timezone

from .models import Container, ContainerTask
from ..assignments.models import Assignment
from ..submissions.models import Submission


@shared_task
def create_containers_for_assigment(assignment_id):
    if settings.DEBUG:
        return

    assignment = Assignment.objects.get(id = assignment_id)

    while assignment.containers.count() < assignment.preferred_num_containers:
        Container.create_container_for_assignment(assignment)
        assignment.refresh_from_db()


@shared_task
def periodic_container_checks():
    if settings.DEBUG:
        return

    for submission in Submission.objects.all():
        if submission.complete and submission.container_task is not None:
            submission.container_task.delete()

    for assignment in Assignment.objects.all():
        if assignment.containers.count() > assignment.preferred_num_containers:
            for container in list(assignment.containers.all()):
                if not container.has_task:
                    try:
                        container.delete()
                    except models.ProtectedError:
                        pass
                    else:
                        container.ensure_stopped()
                        subprocess.call(container.delete_command)

                assignment.refresh_from_db()
                if assignment.containers.count() <= assignment.preferred_num_containers:
                    break
        else:
            while assignment.containers.count() < assignment.preferred_num_containers:
                Container.create_container_for_assignment(assignment)
                assignment.refresh_from_db()

    update_containers()


@shared_task
def update_containers():
    if settings.DEBUG:
        return

    for container in Container.objects.all():
        if not container.has_task:
            try:
                task = ContainerTask.objects.create(container = container, submission = None)
            except IntegrityError:
                pass
            else:
                container.system_upgrade()
                container.install_packages()
            finally:
                if "task" in locals():
                    task.delete()

