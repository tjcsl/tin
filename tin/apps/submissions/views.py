from __future__ import annotations

import psutil
from django import http
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from ..auth.decorators import login_required, superuser_required, teacher_or_superuser_required
from .forms import CommentForm, FilterForm
from .models import Comment, Submission
from .utils import serialize_submission_info

# Create your views here.


@login_required
def show_view(request, submission_id):
    """Show a submission

    Args:
        request: The request
        submission_id: An instance of the :class:`.Submission` model
    """
    submission = get_object_or_404(
        Submission.objects.filter_visible(request.user), id=submission_id
    )

    submissions = Submission.objects.filter(
        student=submission.student, assignment=submission.assignment
    )

    before_submissions = submissions.filter(id__lt=submission.id)
    submission_number = before_submissions.count() + 1

    context = {
        "course": submission.assignment.course,
        "folder": submission.assignment.folder,
        "assignment": submission.assignment,
        "submission": submission,
        "submission_number": submission_number,
        "submission_text": submission.file_text,
        "submission_comments": submission.comments.all(),
        "submissions": submissions.order_by("-date_submitted"),
        "is_student": submission.assignment.course.is_student_in_course(request.user),
        "is_teacher": request.user in submission.assignment.course.teacher.all(),
    }

    if request.user.is_teacher or request.user.is_superuser:
        context["student"] = submission.student

    return render(request, "submissions/show.html", context)


@login_required
def show_json_view(request, submission_id):
    """Get a JSON response about the information of a submission

    Args:
        request: The request
        submission_id: An instance of the :class:`.Submission` model
    """
    try:
        submission = Submission.objects.filter_visible(request.user).get(id=submission_id)
    except Submission.DoesNotExist:
        return http.JsonResponse({"error": "Submission not found"})

    return http.JsonResponse(serialize_submission_info(submission, request.user))


@login_required
def download_view(request, submission_id):
    """Download a submission

    Args:
        request: The request
        submission_id: An instance of the :class:`.Submission` model
    """
    submission = get_object_or_404(
        Submission.objects.filter_visible(request.user), id=submission_id
    )

    file_with_header = submission.file_text_with_header
    language = "P" if submission.assignment.filename.endswith(".py") else "J"
    extension = "java" if language == "J" else "py"
    username = submission.student.username

    response = http.HttpResponse(file_with_header, content_type="text/plain")
    response["Content-Disposition"] = f'attachment; filename="{username}.{extension}"'
    return response


@login_required
def kill_view(request, submission_id):
    """Kill a submission

    Args:
        request: The request
        submission_id: An instance of the :class:`.Submission` model
    """
    submission = get_object_or_404(
        Submission.objects.filter_visible(request.user), id=submission_id
    )

    if request.method == "POST":
        submission.kill_requested = True
        submission.save()
        next_url = request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
            return redirect(next_url)
        else:
            return redirect("submissions:show", submission.id)
    else:
        raise http.Http404


@teacher_or_superuser_required
def rerun_view(request, submission_id):
    """Rerun a submission

    Args:
        request: The request
        submission_id: An instance of the :class:`.Submission` model
    """
    submission = get_object_or_404(
        Submission.objects.filter_visible(request.user), id=submission_id
    )

    submission.rerun().apply_async()
    return redirect("submissions:show", submission.id)


@teacher_or_superuser_required
def comment_view(request, submission_id):
    """Comment on a submission

    Args:
        request: The request
        submission_id: An instance of the :class:`.Submission` model
    """
    if request.method != "POST":
        raise http.Http404

    submission = get_object_or_404(
        Submission.objects.filter_editable(request.user), id=submission_id
    )

    if not submission.complete or not submission.has_been_graded:
        raise http.Http404

    comment = request.POST.get("comment", "")
    point_override = request.POST.get("point_override")

    if point_override is None:
        return http.HttpResponseBadRequest("Missing point_override")

    comment = Comment(
        submission=submission,
        author=request.user,
        start_char=0,
        end_char=len(submission.file_text),
        text=comment,
        point_override=point_override,
    )
    comment.save()

    submission.publish()

    return redirect("submissions:show", submission.id)


@teacher_or_superuser_required
def edit_comment_view(request, submission_id, comment_id):
    """Edit a comment on a submission

    Args:
        request: The request
        submission_id: An instance of the :class:`.Submission` model
        comment_id: An instance of the :class:`.Comment` model
    """
    submission = get_object_or_404(
        Submission.objects.filter_editable(request.user), id=submission_id
    )
    comment = get_object_or_404(submission.comments.all(), id=comment_id)
    assignment = submission.assignment

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect("submissions:show", submission.id)

    before_submissions = Submission.objects.filter(
        student=submission.student, assignment=submission.assignment, id__lt=submission.id
    )
    submission_number = before_submissions.count() + 1

    form = CommentForm(instance=comment)
    context = {
        "form": form,
        "nav_item": "Edit comment",
        "course": assignment.course,
        "folder": assignment.folder,
        "assignment": assignment,
        "submission": submission,
        "comment": comment,
        "submission_number": submission_number,
    }

    return render(request, "submissions/edit_comment.html", context=context)


@teacher_or_superuser_required
def delete_comment_view(request, submission_id, comment_id):
    """Delete a comment

    Args:
        request: The request
        submission_id: An instance of the :class:`.Submission` model
        comment_id: An instance of the :class:`.Comment` model
    """
    submission = get_object_or_404(
        Submission.objects.filter_editable(request.user), id=submission_id
    )
    comment = get_object_or_404(submission.comments.all(), id=comment_id)
    course = submission.assignment.course

    if not course.teacher.filter(id=request.user.id).exists() and not request.user.is_superuser:
        raise http.Http404

    comment.delete()
    return redirect("submissions:show", submission.id)


@teacher_or_superuser_required
def publish_view(request, submission_id):
    """Publish a submission

    Args:
        request: The request
        submission_id: An instance of the :class:`.Submission` model
    """
    submission = get_object_or_404(
        Submission.objects.filter_editable(request.user), id=submission_id
    )

    submission.publish()
    return redirect("submissions:show", submission.id)


@teacher_or_superuser_required
def unpublish_view(request, submission_id):
    """Unpublish a submission

    Args:
        request: The request
        submission_id: An instance of the :class:`.Submission` model
    """
    submission = get_object_or_404(
        Submission.objects.filter_editable(request.user), id=submission_id
    )

    submission.unpublish()
    return redirect("submissions:show", submission.id)


@teacher_or_superuser_required
def filter_view(request):
    """Search through submissions based on a filter.

    Args:
        request: The request
    """
    if request.method == "POST":
        filter_form = FilterForm(request.POST)
        if filter_form.is_valid():
            queryset = filter_form.get_results()

            if "list_submissions" in request.POST:
                return render(
                    request,
                    "submissions/filter.html",
                    {
                        "form": filter_form,
                        "submissions": queryset,
                        "action": "show",
                        "nav_item": "Filter submissions",
                    },
                )
            elif "view_code" in request.POST:
                submission_texts = []
                for submission in queryset:
                    submission_texts.append(submission.file_text)

                return render(
                    request,
                    "submissions/filter.html",
                    {
                        "form": filter_form,
                        "submissions": list(zip(queryset, submission_texts, strict=False)),
                        "action": "show_code",
                        "nav_item": "Filter submissions",
                    },
                )

    filter_form = FilterForm()

    return render(
        request,
        "submissions/filter.html",
        {
            "form": filter_form,
            "submissions": Submission.objects.none(),
            "action": "filter",
            "nav_item": "Filter submissions",
        },
    )


@superuser_required
def set_aborted_complete_view(request):
    """Check if a submission is running.

    This also marks all non-running incomplete submissions
    as completed.

    Args:
        request: The request
    """
    if request.method == "POST":
        submissions = Submission.objects.filter(complete=False, grader_pid__isnull=False)

        for submission in submissions:
            if not psutil.pid_exists(submission.grader_pid):
                submission.complete = True
                submission.grader_pid = None
                submission.save(update_fields=["complete", "grader_pid"])

    return redirect("auth:index")


@superuser_required
def set_past_timeout_complete_view(request):
    """Update submissions based off the time limit

    If it has exceeded its time limit, marks it as complete

    Args:
        request: The request
    """
    if request.method == "POST":
        Submission.objects.filter(
            complete=False,
            grader_start_time__isnull=False,
            assignment__enable_grader_timeout=True,
            grader_start_time__lte=timezone.localtime().timestamp()
            - F("assignment__grader_timeout"),
        ).update(complete=True)

    return redirect("auth:index")
