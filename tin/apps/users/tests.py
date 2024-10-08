from __future__ import annotations

import json

from django.urls import reverse

from tin.tests import login


@login("student")
def test_user_dark_mode(client, student):
    assert student.dark_mode == 0
    response = client.post(reverse("users:theme"), {"dark_mode": 1})
    assert json.loads(response.content.decode("utf-8")).get("success") is True
    student.refresh_from_db()
    assert student.dark_mode == 1
