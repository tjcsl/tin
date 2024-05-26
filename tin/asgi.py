"""
ASGI config for tin project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

from __future__ import annotations

import os

from channels.auth import AuthMiddlewareStack
from channels.generic.websocket import WebsocketConsumer
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tin.settings")
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()


from .apps.submissions.consumers import SubmissionJsonConsumer  # noqa: E402


class WebsocketCloseConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.close()

    def receive(self, text_data: str | None = None, bytes_data: bytes | None = None):
        pass

    def disconnect(self, code):
        pass


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(
                [
                    path("submissions/<int:submission_id>.json", SubmissionJsonConsumer.as_asgi()),
                    path("<path:path>", WebsocketCloseConsumer.as_asgi()),
                ]
            )
        ),
    }
)
