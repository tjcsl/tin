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
                latest_submission = (submissions.latest("date_submitted") if submissions else None)
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
                students_and_submissions = []
                for student in assignment.course.students.all():
                    student_submissions = Submission.objects.filter(student = request.user, assignment = assignment)
                    if student_submissions:
                        students_and_submissions.append((student, student_submissions.latest("date_submitted")))
                    else:
                        students_and_submissions.append((student, None))

                return render(
                    request,
                    "assignments/show.html",
                    {
                        "course": assignment.course,
                        "assignment": assignment,
                    },
                )

    raise http.Http404

