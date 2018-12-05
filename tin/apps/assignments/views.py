from django.shortcuts import render

from .models import Assignment
from ..submissions.models import Submission

# Create your views here.
def show_view(request, assignment_id):
    assignment = Assignment.objects.get(id = assignment_id)
    if request.user.is_student:
        submissions = Submission.objects.filter(student = request.user, assignment = assignment)
        return render(
            request,
            "assignments/show.html",
            {
                "course": assignment.course,
                "assignment": assignment,
                "submissions": submissions,
            },
        )
    else:
        return render(
            request,
            "assignments/show.html",
            {
                "course": assignment.course,
                "assignment": assignment,
            },
        )

