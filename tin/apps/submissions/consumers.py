from typing import Any

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer

from .models import Submission
from .utils import serialize_submission_info


class SubmissionJsonConsumer(JsonWebsocketConsumer):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.submission = None
        self.user = None
        self.connected = False

    def connect(self) -> None:
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            self.close()
            return

        submission_id = self.scope["url_route"]["kwargs"]["submission_id"]

        try:
            self.submission = Submission.objects.get(id=submission_id)
        except Submission.DoesNotExist:
            self.close()
            return

        # A user may watch a submission's live updates only if it is their own
        # submission, or they teach the course, or they are a superuser. The
        # previous check allowed *any* student enrolled in the course to read
        # *any* classmate's submission (including quizzes), which the HTTP views
        # (Submission.objects.filter_visible) never permit.
        is_owner = self.submission.student_id == self.user.id
        is_teacher = self.submission.assignment.course.teacher.filter(id=self.user.id).exists()
        if not (is_owner or is_teacher or self.user.is_superuser):
            self.close()
            return

        self.connected = True
        self.accept()

        async_to_sync(self.channel_layer.group_add)(
            self.submission.channel_group_name, self.channel_name
        )

        self.send_submission_info()

    def disconnect(self, code: int) -> None:
        self.submission = None
        self.user = None
        self.connected = False

    def receive_json(self, content: Any, **kwargs: Any) -> None:
        if self.connected:
            if not isinstance(content, dict):
                return

            msg_type = content.get("type")
            if msg_type == "request-info":
                self.send_submission_info()

    def submission_updated(self, _event) -> None:
        self.send_submission_info()

    def send_submission_info(self):
        if self.connected:
            self.submission.refresh_from_db()
            self.send_json(serialize_submission_info(self.submission, self.user))
