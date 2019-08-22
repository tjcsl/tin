import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tin.settings")

app = Celery("tin")

if not settings.DEBUG:
    app.conf.beat_schedule = {
        "periodic-container-checks": {
            "task": "tin.apps.containers.tasks.periodic_container_checks",
            "schedule": crontab(hour=4, minute=0),
            "args": (),
        }
    }

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
