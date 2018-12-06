from django import http
from django.shortcuts import render

from .models import Assignment
from ..submissions.models import Submission
from ..auth.decorators import login_required

# Create your views here.
@login_required
def show_view(request, assignment_id):
    try:
        assignment = Assignment.objects.get(id = assignment_id)
    except Assignment.DoesNotExist:
        pass
    else:
        if request.user.is_student:
            if assignment.course in request.user.courses.all():
                submissions = Submission.objects.filter(student = request.user, assignment = assignment).order_by("date_submitted")
                latest_submission = submissions[-1]
                return render(
                    request,
                    "assignments/show.html",
                    {
                        "course": assignment.course,
                        "assignment": assignment,
                        "submissions": submissions,
                        "latest_submission": latest_submission,
                    },
                )
        else:
            if request.user == assignment.course.teacher:
                return render(
                    request,
                    "assignments/show.html",
                    {
                        "course": assignment.course,
                        "assignment": assignment,
                    },
                )

    raise http.Http404

