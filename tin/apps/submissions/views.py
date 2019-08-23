from django import http
from django.shortcuts import render

from ..auth.decorators import login_required
from .models import Submission

# Create your views here.


@login_required
def show_view(request, submission_id):
    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        raise http.Http404

    before_submissions = Submission.objects.filter(
        student=submission.student, assignment=submission.assignment, id__lt=submission.id
    )
    submission_number = before_submissions.count() + 1

    submission_text = submission.file.read().decode()

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
                    "submission_text": submission_text,
                },
            )
        else:
            raise http.Http404
    else:
        if request.user == submission.assignment.course.teacher or request.user.is_superuser:
            return render(
                request,
                "submissions/show.html",
                {
                    "course": submission.assignment.course,
                    "assignment": submission.assignment,
                    "submission": submission,
                    "student": submission.student,
                    "submission_number": submission_number,
                    "submission_text": submission_text,
                },
            )
        else:
            raise http.Http404


@login_required
def show_json_view(request, submission_id):
    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        return http.JsonResponse({"error": "Submission not found"})

    if (
        submission.assignment.course in request.user.courses.all()
        or request.user == submission.assignment.course.teacher
        or request.user.is_superuser
    ):
        data = {
            "grader_output": submission.grader_output,
            "grader_errors": submission.grader_errors,
            "has_been_graded": submission.has_been_graded,
            "complete": submission.complete,
            "points_received": (
                str(submission.points_received) if submission.points_received is not None else None
            ),
            "points_possible": (
                str(submission.points_possible) if submission.points_possible is not None else None
            ),
            "grade_percent": submission.grade_percent,
            "formatted_grade": (
                "{}/{} ({})".format(
                    submission.points_received, submission.points_possible, submission.grade_percent
                )
                if submission.has_been_graded
                else "Not graded"
            ),
        }
        if not request.user.is_student:
            data["grader_errors"] = submission.grader_errors
        return http.JsonResponse(data)

    return http.Http404
