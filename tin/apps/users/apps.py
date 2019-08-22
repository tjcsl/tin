from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "tin.apps.users"

    def ready(self):
        from . import signals  # pylint: disable=unused-import # noqa
