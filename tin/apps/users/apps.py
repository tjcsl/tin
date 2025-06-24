from __future__ import annotations

from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "tin.apps.users"

    def ready(self):
        from . import signals  # noqa: F401, PLC0415
