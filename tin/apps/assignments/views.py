import csv
import datetime
import os
import subprocess
import zipfile
from io import BytesIO

from django import http
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.utils.timezone import now

from ... import sandboxing
from ..auth.decorators import login_required, teacher_or_superuser_required
from ..courses.models import Course
from ..submissions.models import Submission
from ..submissions.tasks import run_submission
from ..users.models import User
from .forms import (
    AssignmentForm,
    FileSubmissionForm,
    FolderForm,
    GraderFileSubmissionForm,
    SuperuserFileSubmissionForm,
    TextSubmissionForm,
)
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
                "folder": assignment.folder,
                "assignment": assignment,
                "submissions": submissions,
                "latest_submission": latest_submission,
            },
        )
    else:
        students_and_submissions = []
        new_since_last_login = None
        new_in_last_24 = None
        teacher_last_login = request.user.last_login
        time_24_hours_ago = now() - datetime.timedelta(days=1)

        if request.user not in assignment.course.teacher.all():
            periods_of_user = assignment.course.period_set.all()
        else:
            periods_of_user = assignment.course.period_set.filter(teacher=request.user)
        students_of_user = set()
        for period in periods_of_user:
            for student in period.students.all():
                students_of_user.add(student)

        for student in students_of_user:
            latest_submission = (
                Submission.objects.filter(student=student, assignment=assignment)
                .order_by("-date_submitted")
                .first()
            )
            if latest_submission:
                new_since_last_login = latest_submission.date_submitted > teacher_last_login
                new_in_last_24 = latest_submission.date_submitted > time_24_hours_ago
            period = student.periods.filter(course=assignment.course)
            students_and_submissions.append(
                (student, period, latest_submission, new_since_last_login, new_in_last_24)
            )

        context = {
            "course": assignment.course,
            "folder": assignment.folder,
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
        assignment_form = AssignmentForm(course, request.POST)
        if assignment_form.is_valid():
            assignment = assignment_form.save(commit=False)
            assignment.course = course
            assignment.save()
            return redirect("assignments:show", assignment.id)
    else:
        assignment_form = AssignmentForm(course)
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

    course = assignment.course
    assignment_form = AssignmentForm(course, instance=assignment)
    if request.method == "POST":
        assignment_form = AssignmentForm(course, data=request.POST, instance=assignment)
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
def delete_view(request, assignment_id):
    """Edits an assignment"""
    assignment = get_object_or_404(
        Assignment.objects.filter_editable(request.user), id=assignment_id
    )
    course = assignment.course
    assignment.delete()
    return redirect(reverse("courses:show", args=(course.id,)))


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

    submissions = Submission.objects.filter(student=student, assignment=assignment).order_by(
        "-date_submitted"
    )
    latest_submission = submissions.first() if submissions else None
    latest_submission_text = None
    if latest_submission:
        with open(latest_submission.backup_file_path) as f_obj:
            latest_submission_text = f_obj.read()

    file_form = FileSubmissionForm()
    text_form = TextSubmissionForm(initial={"text": latest_submission_text})

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
    writer.writerow(["Name", "Username", "Period", "Raw Score", "Formatted Grade"])

    for student in assignment.course.students.all().order_by("periods", "last_name"):
        row = []
        row.append(student.full_name)
        row.append(student.username)
        periods = ", ".join([p.name for p in student.periods.filter(course=assignment.course)])
        row.append(periods)
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
def download_submissions_view(request, assignment_id):
    assignment = get_object_or_404(
        Assignment.objects.filter_editable(request.user), id=assignment_id
    )
    name = "assignment_{}_student_submissions.zip".format(assignment.id)

    s = BytesIO()
    zf = zipfile.ZipFile(s, "w")
    for student in assignment.course.students.all():
        latest_submission = (
            Submission.objects.filter(student=student, assignment=assignment)
            .order_by("-date_submitted")
            .first()
        )
        if latest_submission is not None:
            zf.write(latest_submission.file.path, arcname="{}.py".format(student.username))
    zf.close()
    resp = http.HttpResponse(s.getvalue(), content_type="application/x-zip-compressed")
    resp["Content-Disposition"] = "attachment; filename={}".format(name)
    return resp


@teacher_or_superuser_required
def download_log_view(request, assignment_id):
    assignment = get_object_or_404(
        Assignment.objects.filter_editable(request.user), id=assignment_id
    )

    log_file_name = os.path.join(settings.MEDIA_ROOT, assignment.grader_log_filename)

    if (
        request.user not in assignment.course.teacher.all() and not request.user.is_superuser
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


@teacher_or_superuser_required
def create_folder_view(request, course_id):
    course = get_object_or_404(Course.objects.filter_editable(request.user), id=course_id)

    form = FolderForm()
    if request.method == "POST":
        form = FolderForm(request.POST)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.course = course
            folder.save()
            return redirect("courses:show", course.id)

    context = {
        "form": form,
        "nav_item": "Create folder",
        "course": course,
    }

    return render(request, "assignments/add_folder.html", context=context)


@teacher_or_superuser_required
def remove_folder_view(request, course_id, folder_id):
    course = get_object_or_404(Course.objects.filter_editable(request.user), id=course_id)
    folder = get_object_or_404(course.folders.all(), id=folder_id)

    folder.delete()
    return redirect("courses:show", course.id)


@login_required
def show_folder_view(request, course_id, folder_id):
    course = get_object_or_404(Course.objects.filter_editable(request.user), id=course_id)
    folder = get_object_or_404(course.folders.all(), id=folder_id)

    assignments = course.assignments.filter(folder=folder).filter_visible(request.user)
    if course.sort_assignments_by == "due_date":
        assignments = assignments.order_by("-due")
    elif course.sort_assignments_by == "name":
        assignments = assignments.order_by("name")

    context = {
        "course": course,
        "folder": folder,
        "assignments": assignments,
        "period": course.period_set.filter(students=request.user),
    }
    if request.user.is_student:
        context["unsubmitted_assignments"] = assignments.exclude(submissions__student=request.user)

    return render(request, "assignments/show_folder.html", context=context)


@teacher_or_superuser_required
def upload(request):
    if not request.user.is_superuser:
        return redirect("courses:index")

    form = SuperuserFileSubmissionForm()

    file_errors = ""

    if request.method == "POST":
        if request.FILES.get("upload_file"):
            if request.FILES["upload_file"].size <= settings.SUBMISSION_SIZE_LIMIT:
                form = SuperuserFileSubmissionForm(
                    request.POST,
                    request.FILES,
                )
                if form.is_valid():
                    assignment = form.cleaned_data["assignment"]
                    try:
                        text = request.FILES["upload_file"].read().decode()
                    except UnicodeDecodeError:
                        file_errors = "Please don't upload binary files."
                    else:
                        fpath = os.path.join(
                            settings.MEDIA_ROOT,
                            "assignment-{}".format(assignment.id),
                            request.FILES["upload_file"].name,
                        )

                        os.makedirs(os.path.dirname(fpath), exist_ok=True)

                        args = sandboxing.get_assignment_sandbox_args(
                            ["sh", "-c", 'cat >"$1"', "sh", fpath],
                            network_access=False,
                            whitelist=[os.path.dirname(fpath)],
                        )

                        subprocess.run(
                            args,
                            input=text,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE,
                            universal_newlines=True,
                            check=True,
                        )

                        return redirect("courses:index")
                else:
                    file_errors = form.errors
            else:
                file_errors = "That file's too large. Are you sure it's a Python program?"
        else:
            file_errors = "Please select a file."

    return render(
        request,
        "assignments/upload.html",
        {
            "form": form,
            "file_errors": file_errors,
            "nav_item": "Upload file",
        },
    )
