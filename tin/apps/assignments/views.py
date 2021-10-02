import csv
import datetime
import os
import subprocess

from django import http
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.utils.timezone import now

from ... import sandboxing
from ..auth.decorators import login_required, teacher_or_superuser_required
from ..courses.models import Course
from ..submissions.models import Submission
from ..submissions.tasks import run_submission
from ..users.models import User
from .forms import AssignmentForm, FileSubmissionForm, GraderFileSubmissionForm, TextSubmissionForm
from .models import Assignment, CooldownPeriod


@login_required
def show_view(request, assignment_id):
    """
    Shows an overview of the assignment
    :param request: The request
    :param assignment_id: The assignment id
    """
    assignment = get_object_or_404(
        Assignment.objects.filter_visible(request.user), id=assignment_id
    )

    if request.user.is_student and not request.user.is_superuser:
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
        students_and_submissions = []
        new_since_last_login = None
        new_in_last_24 = None
        teacher_last_login = (
            assignment.course.teacher.last_login
            if assignment.course.teacher
            else datetime.datetime(3000, 1, 1)
        )
        time_24_hours_ago = now() - datetime.timedelta(days=1)
        for student in assignment.course.students.all().order_by("last_name"):
            latest_submission = (
                Submission.objects.filter(student=student, assignment=assignment)
                .order_by("-date_submitted")
                .first()
            )
            if latest_submission:
                new_since_last_login = latest_submission.date_submitted > teacher_last_login
                new_in_last_24 = latest_submission.date_submitted > time_24_hours_ago
            students_and_submissions.append(
                (student, latest_submission, new_since_last_login, new_in_last_24)
            )

        context = {
            "course": assignment.course,
            "assignment": assignment,
            "students_and_submissions": students_and_submissions,
            "log_file_exists": (
                assignment.grader_log_filename is not None
                and os.path.exists(
                    os.path.join(settings.MEDIA_ROOT, assignment.grader_log_filename)
                )
            ),
        }

        if request.user.is_student:
            submissions = Submission.objects.filter(
                student=request.user, assignment=assignment
            ).order_by("-date_submitted")
            latest_submission = submissions.first() if submissions else None
            context.update({"submissions": submissions, "latest_submission": latest_submission})

        return render(request, "assignments/show.html", context)


@teacher_or_superuser_required
def create_view(request, course_id):
    """Creates an assignment"""
    course = get_object_or_404(Course.objects.filter_editable(request.user), id=course_id)

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
    """Edits an assignment"""
    assignment = get_object_or_404(
        Assignment.objects.filter_editable(request.user), id=assignment_id
    )

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
    """Uploads a grader for an assignment"""
    assignment = get_object_or_404(
        Assignment.objects.filter_editable(request.user), id=assignment_id
    )

    grader_form = GraderFileSubmissionForm()

    grader_file_errors = ""

    if request.method == "POST":
        if request.FILES.get("grader_file"):
            if request.FILES["grader_file"].size <= settings.SUBMISSION_SIZE_LIMIT:
                grader_form = GraderFileSubmissionForm(
                    request.POST,
                    request.FILES,
                )
                if grader_form.is_valid():
                    try:
                        grader_text = request.FILES["grader_file"].read().decode()
                    except UnicodeDecodeError:
                        grader_file_errors = "Please don't upload binary files."
                    else:
                        assignment.save_grader_file(grader_text)

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
    assignment = get_object_or_404(
        Assignment.objects.filter_editable(request.user), id=assignment_id
    )
    student = get_object_or_404(User, id=student_id)

    submissions = Submission.objects.filter(student=student, assignment=assignment).order_by(
        "-date_submitted"
    )
    latest_submission = submissions.first() if submissions else None

    latest_submission_text = None
    if latest_submission:
        with open(latest_submission.backup_file_path) as f_obj:
            latest_submission_text = f_obj.read()

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
    assignment = get_object_or_404(
        Assignment.objects.filter_visible(request.user), id=assignment_id
    )

    if not request.user.is_student:
        raise http.Http404

    student = request.user

    file_form = FileSubmissionForm()
    text_form = TextSubmissionForm()

    file_errors = ""
    text_errors = ""

    if request.method == "POST":
        if assignment.grader_file is None:
            return redirect("assignments:show", assignment.id)

        if (
            Submission.objects.filter(student=request.user, complete=False).count()
            >= settings.CONCURRENT_USER_SUBMISSION_LIMIT
        ):
            if request.FILES.get("file"):
                file_form = FileSubmissionForm(request.POST, request.FILES)
                file_errors = (
                    "You may only have a maximum of {} submission{} running at the same "
                    "time".format(
                        settings.CONCURRENT_USER_SUBMISSION_LIMIT,
                        "" if settings.CONCURRENT_USER_SUBMISSION_LIMIT == 1 else "s",
                    )
                )
            else:
                text_form = TextSubmissionForm(request.POST)
                text_errors = (
                    "You may only have a maximum of {} submission{} running at the same "
                    "time".format(
                        settings.CONCURRENT_USER_SUBMISSION_LIMIT,
                        "" if settings.CONCURRENT_USER_SUBMISSION_LIMIT == 1 else "s",
                    )
                )
        elif CooldownPeriod.exists(assignment=assignment, student=student):
            cooldown_period = CooldownPeriod.objects.get(assignment=assignment, student=student)

            end_delta = cooldown_period.get_time_to_end()
            # Throw out the microseconds
            end_delta = datetime.timedelta(days=end_delta.days, seconds=end_delta.seconds)

            if request.FILES.get("file"):
                file_form = FileSubmissionForm(request.POST, request.FILES)
                file_errors = (
                    "You have made too many submissions too quickly. You will be able to re-submit"
                    "in {}.".format(end_delta)
                )
            else:
                text_form = TextSubmissionForm(request.POST)
                text_errors = (
                    "You have made too many submissions too quickly. You will be able to re-submit"
                    "in {}.".format(end_delta)
                )
        else:
            if request.FILES.get("file"):
                if request.FILES["file"].size <= settings.SUBMISSION_SIZE_LIMIT:
                    file_form = FileSubmissionForm(request.POST, request.FILES)
                    if file_form.is_valid():
                        try:
                            submission_text = request.FILES["file"].read().decode()
                        except UnicodeDecodeError:
                            file_errors = "Please don't upload binary files."
                        else:
                            submission = Submission()
                            submission.assignment = assignment
                            submission.student = student
                            submission.save_file(submission_text)
                            submission.save()

                            assignment.check_rate_limit(student)

                            submission.create_backup_copy(submission_text)

                            run_submission.delay(submission.id)
                            return redirect("assignments:show", assignment.id)
                else:
                    file_errors = "That file's too large. Are you sure it's a Python program?"
            else:
                text_form = TextSubmissionForm(request.POST)
                if text_form.is_valid():
                    submission_text = text_form.cleaned_data["text"]
                    if len(submission_text) <= settings.SUBMISSION_SIZE_LIMIT:
                        submission = text_form.save(commit=False)
                        submission.assignment = assignment
                        submission.student = student
                        submission.save_file(submission_text)
                        submission.save()

                        assignment.check_rate_limit(student)

                        submission.create_backup_copy(submission_text)

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
    assignment = get_object_or_404(
        Assignment.objects.filter_editable(request.user), id=assignment_id
    )

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
    assignment = get_object_or_404(
        Assignment.objects.filter_editable(request.user), id=assignment_id
    )

    log_file_name = os.path.join(settings.MEDIA_ROOT, assignment.grader_log_filename)

    if (
        request.user != assignment.course.teacher and not request.user.is_superuser
    ) or not os.path.exists(log_file_name):
        raise http.Http404

    assigment_dir = os.path.dirname(log_file_name)

    args = sandboxing.get_assignment_sandbox_args(
        ["cat", "--", log_file_name],
        network_access=False,
        whitelist=[assigment_dir],
        read_only=[assigment_dir],
    )

    res = subprocess.run(
        args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=True,
    )

    data = res.stdout

    response = http.HttpResponse(data, content_type="text/plain")
    response["Content-Disposition"] = 'attachment; filename="{}-grader.log"'.format(
        slugify(assignment.name)
    )

    return response
