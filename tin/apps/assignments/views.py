from django import http
from django.shortcuts import render, get_object_or_404

from .models import Assignment
from ..submissions.models import Submission
from ..users.models import User
from ..auth.decorators import login_required, teacher_or_superuser_required

# Create your views here.
@login_required
def show_view(request, assignment_id):
    assignment = get_object_or_404(Assignment, id = assignment_id)

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
            raise http.Http404
    else:
        if request.user.is_superuser or request.user == assignment.course.teacher:
            students_and_submissions = []
            for student in assignment.course.students.all():
                student_submissions = Submission.objects.filter(student = student, assignment = assignment)
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
                    "students_and_submissions": students_and_submissions,
                },
            )
        else:
            raise http.Http404

@teacher_or_superuser_required
def student_submission_view(request, assignment_id, student_id):
    assignment = get_object_or_404(Assignment, id = assignment_id)
    student = get_object_or_404(User, id = student_id)

    submissions = Submission.objects.filter(student = student, assignment = assignment).order_by("date_submitted")
    latest_submission = (submissions.latest("date_submitted") if submissions else None)

    return render(
        request,
        "assignments/student_submission.html",
        {
            "course": assignment.course,
            "assignment": assignment,
            "student": student,
            "submissions": submissions,
            "latest_submission": latest_submission,
        },
    )
