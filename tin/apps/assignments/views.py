from django.shortcuts import render

from .models import Assignment
from ..submissions.models import Submission

# Create your views here.
def show_view(request, assignment_id):
    assignment = Assignment.objects.get(id = assignment_id)
    if not request.user.is_staff:
        submissions = Submission.objects.filter(student = request.user, assignment = assignment)
        return render(
            request,
            "assignments/show.html",
            {
                "assignment": assignment,
                "submissions": submission,
            },
        )
    else:
        return render(
            request,
            "assignments/show.html",
            {
                "assignment": assignment,
            },
        )

