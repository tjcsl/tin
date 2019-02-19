from django import http
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404

from .models import Course, StudentImport
from .forms import CourseForm
from ..assignments.models import Assignment
from ..auth.decorators import login_required, teacher_or_superuser_required


# Create your views here.
@login_required
def index_view(request):
    """ Lists all courses """
    if request.user.is_superuser:
        courses = Course.objects.all()
    elif request.user.is_teacher:
        courses = Course.objects.filter(teacher = request.user)
    else:
        courses = request.user.courses.all()

    courses = courses.order_by("-created")

    context = {
        "courses": courses,
    }

    if request.user.is_student:
        courses_with_unsubmitted_assignments = set()
        unsubmitted_assignments = []
        for course in courses.all():
            for assignment in course.assignments.all():
                if not assignment.submissions_from_student(request.user):
                    unsubmitted_assignments.append(assignment)
                    courses_with_unsubmitted_assignments.add(course)

        context["courses_with_unsubmitted_assignments"] = courses_with_unsubmitted_assignments
        context["unsubmitted_assignments"] = unsubmitted_assignments

        now = timezone.now()
        context["due_soon_assignments"] = Assignment.objects.filter(course__students = request.user, due__gte = timezone.now(), due__lte = timezone.now() + timezone.timedelta(weeks = 1))

    return render(request, "courses/home.html", context)


@login_required
def show_view(request, course_id):
    """ Lists information about a course """
    course = get_object_or_404(Course, id = course_id)
    if request.user.is_superuser or course in request.user.courses.all() or request.user == course.teacher:
        assignments = course.assignments.order_by("-due")
        context = {
            "course": course,
            "assignments": assignments,
        }
        if request.user.is_student:
            context["unsubmitted_assignments"] = [assignment for assignment in assignments.all() if not assignment.submissions_from_student(request.user)]

        return render(request, "courses/show.html", context)
    else:
        raise http.Http404


@teacher_or_superuser_required
def create_view(request):
    """ Creates a course """
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit = True)
            course.teacher = request.user
            course.save()
            return redirect("courses:show", course.id)
    else:
        form = CourseForm()
    return render(
        request,
        "courses/edit_create.html",
        {
            "form": form,
            "nav_item": "Create course",
        },
    )


@teacher_or_superuser_required
def edit_view(request, course_id):
    """ Edits a course """
    course = get_object_or_404(Course, id = course_id)

    if request.user != course.teacher and not request.user.is_superuser:
        raise http.Http404

    if request.method == "POST":
        form = CourseForm(data = request.POST, instance = course)
        if form.is_valid():
            course = form.save()
            return redirect("courses:show", course.id)
    else:
        form = CourseForm(instance = course)

    return render(
        request,
        "courses/edit_create.html",
        {
            "form": form,
            "course": course,
            "nav_item": "Edit",
        },
    )


@teacher_or_superuser_required
def import_students_view(request, course_id):
    course = get_object_or_404(Course, id = course_id)

    if request.user != course.teacher and not request.user.is_superuser:
        raise http.Http404

    student_import = StudentImport.objects.get_or_create(course = course)[0]

    if request.method == "POST":
        students = request.POST.get("students", "").splitlines()
        students = [x.strip() for x in students if x.strip()]
        student_import.queue_users(students)
        return redirect("courses:show", course.id)

    return render(
        request,
        "courses/import_students.html",
        {
            "course": course,
            "nav_item": "Import Students",
            "unimported_users": student_import.students.all(),
        },
    )


@teacher_or_superuser_required
def students_view(request, course_id):
    """ View students enrolled in a course """
    course = get_object_or_404(Course, id = course_id)

    if request.user != course.teacher and not request.user.is_superuser:
        raise http.Http404

    students = course.students.all()

    students_missing_assignments = [(student, [assignment.name for assignment in course.assignments.all() if not len(assignment.submissions_from_student(student))]) for student in students]

    return render(
        request,
        "courses/students.html",
        {
            "course": course,
            "students_missing_assignments": students_missing_assignments,
            "nav_item": "Students",
        },
    )
