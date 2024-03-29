import logging
import subprocess
import sys

from celery import shared_task

from django.conf import settings

from .models import Venv, VenvCreationError, VenvExistsError

logger = logging.getLogger(__name__)


@shared_task
def create_venv(venv_id):
    venv = Venv.objects.get(id=venv_id)

    success = False
    try:
        try:
            res = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "virtualenv",
                    "-p",
                    settings.SUBMISSION_PYTHON,
                    "--",
                    venv.path,
                ],
                check=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except FileNotFoundError as e:
            logger.error("Cannot run processes: %s", e)
            raise FileNotFoundError from e

        if res.returncode != 0:
            raise VenvCreationError(
                "Error creating virtual environment (return code {}): {}".format(
                    res.returncode, res.stdout
                )
            )

        venv.fully_created = True
        venv.save()
        success = True
    finally:
        if not success:
            venv.delete()


@shared_task
def install_packages(venv_id, package_names):
    venv = Venv.objects.get(id=venv_id)

    venv.install_packages(package_names)
