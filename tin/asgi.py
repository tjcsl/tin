"""
ASGI config for tin project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from typing import Optional

from channels.auth import AuthMiddlewareStack
from channels.generic.websocket import WebsocketConsumer
from channels.routing import ProtocolTypeRouter, URLRouter

from django.core.asgi import get_asgi_application
from django.urls import path

from .apps.submissions.consumers import SubmissionJsonConsumer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tin.settings")


class WebsocketCloseConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.close()

    def receive(self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None):
        pass

    def disconnect(self, code):
        pass


application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
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
