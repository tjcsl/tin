from django import http
from django.shortcuts import render

from .models import Submission

# Create your views here.
def show_view(request, submission_id):
    try:
        submission = Submission.objects.get(id = submission_id)
    except Assignment.DoesNotExist:
        raise http.Http404

    student_submissions = Submission.objects.filter(student = submission.student, assignment = submission.assignment).order_by("date_submitted")
    submission_number = list(student_submissions).index(submission) + 1
    if request.user.is_student:
        if submission.assignment.course in request.user.courses.all():
            return render(
                request,
                "submissions/show.html",
                {
                    "course": submission.assignment.course,
                    "assignment": submission.assignment,
                    "submission": submission,
                    "submission_number": submission_number,
                },
            )
        else:
            raise http.Http404
    else:
        if request.user == submission.assignment.course.teacher:
            return render(
                request,
                "submissions/show.html",
                {
                    "course": submission.assignment.course,
                    "assignment": submission.assignment,
                    "submission": submission,
                    "student": submission.student,
                    "submission_number": submission_number,
                },
            )
        else:
            raise http.Http404
