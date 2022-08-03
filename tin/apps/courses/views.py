from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..assignments.models import Assignment
from ..auth.decorators import login_required, teacher_or_superuser_required
from .forms import CourseForm, PeriodForm, StudentForm
from .models import Course, Period, StudentImport


# Create your views here.
@login_required
def index_view(request):
    """Lists all courses"""
    courses = Course.objects.filter_visible(request.user).order_by("-created")

    context = {"courses": courses}

    if request.user.is_student:
        unsubmitted_assignments = (
            Assignment.objects.filter_visible(request.user)
            .filter(course__in=request.user.courses.all())
            .exclude(submissions__student=request.user)
        )
        courses_with_unsubmitted_assignments = set(
            assignment.course for assignment in unsubmitted_assignments
        )

        context["courses_with_unsubmitted_assignments"] = courses_with_unsubmitted_assignments
        context["unsubmitted_assignments"] = unsubmitted_assignments

        now = timezone.now()
        context["due_soon_assignments"] = Assignment.objects.filter_visible(request.user).filter(
            course__students=request.user, due__gte=now, due__lte=now + timezone.timedelta(weeks=1)
        )

        context["all_assignments"] = Assignment.objects.filter_visible(request.user).filter(
            course__students=request.user
        )

    return render(request, "courses/home.html", context)


@login_required
def show_view(request, course_id):
    """Lists information about a course"""
    course = get_object_or_404(Course.objects.filter_visible(request.user), id=course_id)

    folders = course.folders.all()

    assignments = course.assignments.filter(folder=None).filter_visible(request.user)
    if course.sort_assignments_by == "due_date":
        assignments = assignments.order_by("-due")
    elif course.sort_assignments_by == "name":
        assignments = assignments.order_by("name")

    context = {
        "course": course,
        "folders": folders,
        "assignments": assignments,
        "period": course.period_set.filter(students=request.user),
    }
    if request.user.is_student:
        context["unsubmitted_assignments"] = assignments.exclude(submissions__student=request.user)

    return render(request, "courses/show.html", context)


@teacher_or_superuser_required
def create_view(request):
    """Creates a course"""
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=True)
            course.teacher = request.user
            course.save()
            return redirect("courses:show", course.id)
    else:
        form = CourseForm()
    return render(request, "courses/edit_create.html", {"form": form, "nav_item": "Create course"})


@teacher_or_superuser_required
def edit_view(request, course_id):
    """Edits a course"""
    course = get_object_or_404(Course.objects.filter_editable(request.user), id=course_id)

    if request.method == "POST":
        form = CourseForm(data=request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            return redirect("courses:show", course.id)
    else:
        form = CourseForm(instance=course)

    return render(
        request, "courses/edit_create.html", {"form": form, "course": course, "nav_item": "Edit"}
    )


@teacher_or_superuser_required
def import_students_view(request, course_id):
    course = get_object_or_404(Course.objects.filter_editable(request.user), id=course_id)

    student_import = StudentImport.objects.get_or_create(course=course)[0]

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
            "nav_item": "Import students",
            "unimported_users": student_import.students.all(),
        },
    )


@teacher_or_superuser_required
def manage_students_view(request, course_id):
    """Add/remove students from a coure"""
    course = get_object_or_404(Course.objects.filter_editable(request.user), id=course_id)

    if request.method == "POST":
        form = StudentForm(data=request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            return redirect("courses:students", course.id)
    else:
        form = StudentForm(instance=course)

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
def students_view(request, course_id):
    """View students enrolled in a course"""
    course = get_object_or_404(Course.objects.filter_editable(request.user), id=course_id)

    if request.user.is_superuser:
        periods = course.period_set.order_by("teacher")
    else:
        periods = course.period_set.filter(teacher=request.user)

    students_by_period = [
        [
            p,
            [
                [
                    s,
                    [
                        assignment.name
                        for assignment in Assignment.objects.filter_visible(request.user)
                        .filter(course=course)
                        .exclude(submissions__student=s)
                    ],
                ]
                for s in p.students.all()
            ],
        ]
        for p in periods
    ]

    students_with_period = [
        [s, course.period_set.filter(students=s)] for s in course.students.all()
    ]

    return render(
        request,
        "courses/students.html",
        {
            "course": course,
            "students": students_with_period,
            "students_by_period": students_by_period,
            "nav_item": "Students",
            "period": course.period_set.filter(students=request.user),
        },
    )


@teacher_or_superuser_required
def add_period_view(request, course_id):
    """Creates a period and associated it with a course"""
    course = get_object_or_404(Course.objects.filter_editable(request.user), id=course_id)

    if request.method == "POST":
        form = PeriodForm(course, request.POST)
        if form.is_valid():
            period = form.save(commit=True)
            period.course = course
            period.save()
            return redirect("courses:students", course.id)
    else:
        form = PeriodForm(course)
    return render(
        request,
        "courses/edit_create.html",
        {"form": form, "course": course, "nav_item": "Create period"},
    )


@teacher_or_superuser_required
def edit_period_view(request, course_id, period_id):
    """Edits a period"""
    course = get_object_or_404(Course.objects.filter_editable(request.user), id=course_id)
    period = get_object_or_404(Period, id=period_id)

    if request.method == "POST":
        form = PeriodForm(course, data=request.POST, instance=period)
        if form.is_valid():
            period = form.save()
            return redirect("courses:students", course.id)
    else:
        form = PeriodForm(course, instance=period)

    return render(
        request,
        "courses/edit_create.html",
        {"form": form, "course": course, "nav_item": "Edit Period"},
    )
