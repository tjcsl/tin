import csv
import os

from django import http
from django.conf import settings
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from ..auth.decorators import login_required, teacher_or_superuser_required
from ..courses.models import Course
from ..submissions.models import Submission, upload_submission_file_path
from ..submissions.tasks import run_submission
from ..users.models import User
from .forms import AssignmentForm, FileSubmissionForm, GraderFileSubmissionForm, TextSubmissionForm
from .models import Assignment


@login_required
def show_view(request, assignment_id):
    """
    Shows an overview of the assignment
    :param request: The request
    :param assignment_id: The assignment id
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)

    if request.user.is_student:
        if assignment.course in request.user.courses.all():
            submissions = Submission.objects.filter(
                student=request.user, assignment=assignment
            ).order_by("-date_submitted")
            latest_submission = submissions.first() if submissions else None

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
            raise http.Http404
    else:
        if request.user.is_superuser or request.user == assignment.course.teacher:
            students_and_submissions = []
            for student in assignment.course.students.all():
                latest_submission = (
                    Submission.objects.filter(student=student, assignment=assignment)
                    .order_by("-date_submitted")
                    .first()
                )
                students_and_submissions.append((student, latest_submission))

            return render(
                request,
                "assignments/show.html",
                {
                    "course": assignment.course,
                    "assignment": assignment,
                    "students_and_submissions": students_and_submissions,
                    "log_file_exists": (
                        assignment.grader_log_filename is not None
                        and os.path.exists(
                            os.path.join(settings.MEDIA_ROOT, assignment.grader_log_filename)
                        )
                    ),
                },
            )
        else:
            raise http.Http404


@teacher_or_superuser_required
def create_view(request, course_id):
    """ Creates an assignment """
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher and not request.user.is_superuser:
        raise http.Http404

    if request.method == "POST":
        assignment_form = AssignmentForm(request.POST)
        if assignment_form.is_valid():
            assignment = assignment_form.save(commit=False)
            assignment.course = course
            assignment.save()
            return redirect("assignments:show", assignment.id)
    else:
        assignment_form = AssignmentForm()
    return render(
        request,
        "assignments/edit_create.html",
        {
            "assignment_form": assignment_form,
            "course": course,
            "action": "add",
            "nav_item": "Create assignment",
        },
    )


@teacher_or_superuser_required
def edit_view(request, assignment_id):
    """ Edits an assignment """
    assignment = get_object_or_404(Assignment, id=assignment_id)

    if request.user != assignment.course.teacher and not request.user.is_superuser:
        raise http.Http404

    assignment_form = AssignmentForm(instance=assignment)
    if request.method == "POST":
        assignment_form = AssignmentForm(data=request.POST, instance=assignment)
        if assignment_form.is_valid():
            assignment_form.save()
            return redirect("assignments:show", assignment.id)

    return render(
        request,
        "assignments/edit_create.html",
        {
            "assignment_form": assignment_form,
            "course": assignment.course,
            "assignment": assignment,
            "action": "edit",
            "nav_item": "Edit",
        },
    )


@teacher_or_superuser_required
def upload_grader_view(request, assignment_id):
    """ Uploads a grader for an assignment """
    assignment = get_object_or_404(Assignment, id=assignment_id)

    if request.user != assignment.course.teacher and not request.user.is_superuser:
        raise http.Http404

    grader_form = GraderFileSubmissionForm(instance=assignment)

    grader_file_errors = ""

    if request.method == "POST":
        if request.FILES.get("grader_file"):
            if request.FILES["grader_file"].size <= settings.SUBMISSION_SIZE_LIMIT:
                if assignment.grader_file.name:
                    old_grader_file_path = assignment.grader_file.path  # LEAVE THIS HERE

                grader_form = GraderFileSubmissionForm(
                    request.POST, request.FILES, instance=assignment
                )
                if grader_form.is_valid():
                    try:
                        request.FILES["grader_file"].read().decode()
                    except UnicodeDecodeError:
                        grader_file_errors = "Please don't upload binary files."
                    else:
                        if "old_grader_file_path" in locals():
                            if os.path.exists(old_grader_file_path):
                                os.remove(old_grader_file_path)

                        grader_form.save()

                        return redirect("assignments:show", assignment.id)
                else:
                    grader_file_errors = grader_form.errors
            else:
                grader_file_errors = "That file's too large. Are you sure it's a Python program?"
        else:
            grader_file_errors = "Please select a file."

    return render(
        request,
        "assignments/upload_grader.html",
        {
            "grader_form": grader_form,
            "grader_file_errors": grader_file_errors,
            "course": assignment.course,
            "assignment": assignment,
            "nav_item": "Upload grader",
        },
    )


@teacher_or_superuser_required
def student_submission_view(request, assignment_id, student_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    student = get_object_or_404(User, id=student_id)

    if request.user != assignment.course.teacher and not request.user.is_superuser:
        raise http.Http404

    submissions = Submission.objects.filter(student=student, assignment=assignment).order_by(
        "-date_submitted"
    )
    latest_submission = submissions.first() if submissions else None

    latest_submission_text = None
    if latest_submission:
        latest_submission_text = latest_submission.file.read().decode()

    return render(
        request,
        "assignments/student_submission.html",
        {
            "course": assignment.course,
            "assignment": assignment,
            "student": student,
            "submissions": submissions,
            "latest_submission": latest_submission,
            "latest_submission_text": latest_submission_text,
        },
    )


@login_required
def submit_view(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)

    if request.user not in assignment.course.students.all():
        raise http.Http404
    student = request.user

    file_form = FileSubmissionForm()
    text_form = TextSubmissionForm()

    file_errors = ""
    text_errors = ""

    if request.method == "POST":
        if assignment.grader_file is None:
            return redirect("assignments:show", assignment.id)
        elif request.FILES.get("file"):
            if request.FILES["file"].size <= settings.SUBMISSION_SIZE_LIMIT:
                file_form = FileSubmissionForm(request.POST, request.FILES)
                if file_form.is_valid():
                    try:
                        request.FILES["file"].read().decode()
                    except UnicodeDecodeError:
                        file_errors = "Please don't upload binary files."
                    else:
                        submission = file_form.save(commit=False)
                        submission.assignment = assignment
                        submission.student = student
                        submission.save()
                        run_submission.delay(submission.id)
                        return redirect("assignments:show", assignment.id)
            else:
                file_errors = "That file's too large. Are you sure it's a Python program?"
        else:
            text_form = TextSubmissionForm(request.POST)
            if text_form.is_valid():
                if len(text_form.cleaned_data["text"]) <= settings.SUBMISSION_SIZE_LIMIT:
                    submission = text_form.save(commit=False)
                    submission.assignment = assignment
                    submission.student = student
                    submission.file.save(
                        upload_submission_file_path(submission, ""),
                        ContentFile(text_form.cleaned_data["text"]),
                        save=False,
                    )
                    submission.save()
                    run_submission.delay(submission.id)
                    return redirect("assignments:show", assignment.id)
                else:
                    text_errors = "Submission too large"

    return render(
        request,
        "assignments/submit.html",
        {
            "file_form": file_form,
            "text_form": text_form,
            "file_errors": file_errors,
            "text_errors": text_errors,
            "course": assignment.course,
            "assignment": assignment,
            "nav_item": "Submit",
        },
    )


@teacher_or_superuser_required
def scores_csv_view(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)

    if request.user != assignment.course.teacher and not request.user.is_superuser:
        raise http.Http404

    response = http.HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="scores.csv"'

    writer = csv.writer(response)
    writer.writerow(["Name", "Username", "Raw Score", "Formatted Grade"])

    for student in assignment.course.students.all():
        row = []
        row.append(student.full_name)
        row.append(student.username)
        latest_submission = (
            Submission.objects.filter(student=student, assignment=assignment)
            .order_by("-date_submitted")
            .first()
        )
        if latest_submission is not None:
            if latest_submission.points_received:
                row.append(latest_submission.points_received)
                row.append(latest_submission.formatted_grade)
            else:
                row.append("NG")
                row.append("NG")
        else:
            row.append("M")
            row.append("M")
        writer.writerow(row)

    return response


@teacher_or_superuser_required
def download_log_view(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)

    if assignment.grader_log_filename is None:
        raise http.Http404

    log_file_name = os.path.join(settings.MEDIA_ROOT, assignment.grader_log_filename)

    if (
        request.user != assignment.course.teacher and not request.user.is_superuser
    ) or not os.path.exists(log_file_name):
        raise http.Http404

    with open(log_file_name) as f_obj:
        data = f_obj.read()

    response = http.HttpResponse(data, content_type="text/plain")
    response["Content-Disposition"] = 'attachment; filename="{}-grader.log"'.format(
        slugify(assignment.name)
    )

    return response
