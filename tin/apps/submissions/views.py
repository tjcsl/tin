import psutil

from django import http
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..auth.decorators import login_required, superuser_required
from .models import Submission
from .utils import serialize_submission_info

# Create your views here.


@login_required
def show_view(request, submission_id):
    submission = get_object_or_404(
        Submission.objects.filter_visible(request.user), id=submission_id
    )

    before_submissions = Submission.objects.filter(
        student=submission.student, assignment=submission.assignment, id__lt=submission.id
    )
    submission_number = before_submissions.count() + 1

    with open(submission.backup_file_path) as f_obj:
        submission_text = f_obj.read()

    context = {
        "course": submission.assignment.course,
        "folder": submission.assignment.folder,
        "assignment": submission.assignment,
        "submission": submission,
        "submission_number": submission_number,
        "submission_text": submission_text,
        "is_student": submission.assignment.course.is_student_in_course(request.user),
        "is_teacher": request.user in submission.assignment.course.teacher.all(),
    }

    if request.user.is_teacher:
        context["student"] = submission.student

    return render(request, "submissions/show.html", context)


@login_required
def show_json_view(request, submission_id):
    try:
        submission = Submission.objects.filter_visible(request.user).get(id=submission_id)
    except Submission.DoesNotExist:
        return http.JsonResponse({"error": "Submission not found"})

    return http.JsonResponse(serialize_submission_info(submission, request.user))


@login_required
def kill_view(request, submission_id):
    submission = get_object_or_404(
        Submission.objects.filter_editable(request.user), id=submission_id
    )

    if request.method == "POST":
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
