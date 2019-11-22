import psutil

from django import http
from django.db.models import F
from django.shortcuts import redirect, render
from django.utils import timezone

from ..auth.decorators import login_required, superuser_required
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
            "has_been_graded": submission.has_been_graded,
            "complete": submission.complete,
            "kill_requested": submission.kill_requested,
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
        if request.user.is_teacher or request.user.is_superuser:
            data["grader_errors"] = submission.grader_errors
        return http.JsonResponse(data)

    return http.Http404


@login_required
def kill_view(request, submission_id):
    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        raise http.Http404

    if request.method == "POST" and (
        (request.user.is_student and submission.assignment.course in request.user.courses.all())
        or request.user == submission.assignment.course.teacher
        or request.user.is_superuser
    ):
        submission.kill_requested = True
        submission.save()
        if request.GET.get("next"):
            return redirect(request.GET["next"])
        else:
            return redirect("submissions:show", submission.id)
    else:
        raise http.Http404


@superuser_required
def set_aborted_complete_view(request):
    if request.method == "POST":
        submissions = Submission.objects.filter(complete=False, grader_pid__isnull=False)

        for submission in submissions:
            try:
                psutil.Process(submission.grader_pid)
            except psutil.NoSuchProcess:
                submission.complete = True
                submission.save(update_fields=["complete"])

    return redirect("auth:index")


@superuser_required
def set_past_timeout_complete_view(request):
    if request.method == "POST":
        Submission.objects.filter(
            complete=False,
            grader_start_time__isnull=False,
            assignment__enable_grader_timeout=True,
            grader_start_time__lte=timezone.localtime().timestamp()
            - F("assignment__grader_timeout"),
        ).update(complete=True)

    return redirect("auth:index")
