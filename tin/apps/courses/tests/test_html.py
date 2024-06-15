from __future__ import annotations

from django.urls import reverse

from tin.tests import Parser, login


@login("teacher")
def test_show_view(client, course, teacher):
    response = client.get(reverse("courses:index"))
    html = Parser.from_response(response)
    assert course.name in html
    assert teacher.last_name in html
