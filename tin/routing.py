from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from django.urls import path

from .apps.submissions.consumers import SubmissionJsonConsumer

application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(
            URLRouter(
                [
                    path("submissions/<int:submission_id>.json", SubmissionJsonConsumer),
                ]
            )
        )
    }
)
