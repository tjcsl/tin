import psutil

from django import http
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..auth.decorators import login_required, superuser_required, teacher_or_superuser_required
from .models import Submission, Comment
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

    with open(submission.backup_file_path, "r", encoding="utf-8") as f_obj:
        submission_text = f_obj.read()

    context = {
        "course": submission.assignment.course,
        "folder": submission.assignment.folder,
        "assignment": submission.assignment,
        "submission": submission,
        "submission_number": submission_number,
        "submission_text": submission_text,
        "submission_comments": submission.comments.all(),
        "is_student": submission.assignment.course.is_student_in_course(request.user),
        "is_teacher": request.user in submission.assignment.course.teacher.all(),
    }

    if request.user.is_teacher or request.user.is_superuser:
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


@teacher_or_superuser_required
def comment_view(request, submission_id):
    submission = get_object_or_404(
        Submission.objects.filter_editable(request.user), id=submission_id
    )

    if not submission.complete or not submission.has_been_graded:
        raise http.Http404

    before_submissions = Submission.objects.filter(
        student=submission.student, assignment=submission.assignment, id__lt=submission.id
    )
    submission_number = before_submissions.count() + 1

    with open(submission.backup_file_path, "r", encoding="utf-8") as f_obj:
        submission_text = f_obj.read()

    if request.method == "POST":
        comment = request.POST.get("comment", "")
        point_override = request.POST.get("point_override", "")
        comment = Comment(
            submission=submission,
            author=request.user,
            start_char=0,
            end_char=len(submission_text),
            text=comment,
            point_override=point_override,
        )
        comment.save()
        return redirect("submissions:show", submission.id)

    context = {
        "course": submission.assignment.course,
        "folder": submission.assignment.folder,
        "assignment": submission.assignment,
        "submission": submission,
        "nav_item": "Comment",
        "submission_number": submission_number,
        "submission_text": submission_text,
    }

    return render(request, "submissions/comment.html", context)


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
