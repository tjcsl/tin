from datetime import date

from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..assignments.models import Assignment
from ..auth.decorators import login_required, teacher_or_superuser_required
from .forms import (
    CourseForm,
    PeriodForm,
    StudentForm,
    SelectCourseToImportFromForm,
    ImportFromSelectedCourseForm,
)
from .models import Course, Period, StudentImport


# Create your views here.
@login_required
def index_view(request):
    """Lists all courses"""
    courses = Course.objects.filter_visible(request.user).order_by("-created")

    context = {"courses": courses}

    if request.user.is_student:
        assignments = (
            Assignment.objects.filter_visible(request.user)
            .filter(course__students=request.user, quiz__isnull=True)
            .order_by("due")
        )

        unsubmitted_assignments = assignments.exclude(submissions__student=request.user)
        context["unsubmitted_assignments"] = unsubmitted_assignments
        context["courses_with_unsubmitted_assignments"] = set(
            assignment.course for assignment in unsubmitted_assignments
        )

        now = timezone.now()
        due_soon_assignments = assignments.filter(
            due__gte=now, due__lte=now + timezone.timedelta(weeks=1)
        )
        context["due_soon_assignments"] = due_soon_assignments

    return render(request, "courses/home.html", context)


@login_required
def show_view(request, course_id):
    """Lists information about a course"""
    course = get_object_or_404(Course.objects.filter_visible(request.user), id=course_id)

    is_teacher = request.user in course.teacher.all()
    if request.user.is_superuser or is_teacher:
        folders = course.folders.order_by("name")
    else:
        folders = course.folders.filter(assignments__hidden=False).distinct().order_by("name")

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
        "is_student": course.is_student_in_course(request.user),
        "is_teacher": is_teacher,
    }
    if course.is_student_in_course(request.user):
        context["unsubmitted_assignments"] = assignments.exclude(submissions__student=request.user)

    return render(request, "courses/show.html", context)


@teacher_or_superuser_required
def create_view(request):
    """Creates a course"""
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=True)
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
def import_select_course_view(request, course_id):
    """Select another course to import assignments or folders from"""
    course = get_object_or_404(Course.objects.filter_editable(request.user), id=course_id)

    courses = Course.objects.filter_editable(request.user).exclude(id=course_id)

    if request.method == "POST":
        form = SelectCourseToImportFromForm(data=request.POST, courses=courses)
        if form.is_valid():
            other_course = form.cleaned_data["course"]
            return redirect("courses:import_from_selected_course", course.id, other_course.id)
    else:
        form = SelectCourseToImportFromForm(courses=courses)

    return render(
        request,
        "courses/import_select_course.html",
        {"form": form, "course": course, "nav_item": "Import"},
    )


@teacher_or_superuser_required
def import_from_selected_course(request, course_id, other_course_id):
    """Select folders and assignments to import from another course"""
    course = get_object_or_404(Course.objects.filter_editable(request.user), id=course_id)
    other_course = get_object_or_404(
        Course.objects.filter_editable(request.user), id=other_course_id
    )

    if request.method == "POST":
        form = ImportFromSelectedCourseForm(data=request.POST, course=other_course)
        if form.is_valid():
            assignments_to_process = []

            # Import folders
            if form.cleaned_data["folders"]:
                for folder in form.cleaned_data["folders"]:
                    assignments = list(folder.assignments.all())
                    folder.pk = None
                    folder.course = course
                    folder.save()
                    for assignment in assignments:
                        assignments_to_process.append((assignment, course, folder))

            # Import assignments
            if form.cleaned_data["assignments"]:
                for assignment in form.cleaned_data["assignments"]:
                    assignments_to_process.append((assignment, course, None))

            for assignment, course, folder in assignments_to_process:
                old_id = assignment.id

                # Save as new
                assignment.pk = None

                # Update course, folder, assigned date, and grader file
                assignment.course = course
                if folder:
                    assignment.folder = folder
                assignment.assigned = timezone.now()
                assignment.grader_file = None

                # Some user options need to be applied before saving
                if form.cleaned_data["hide"]:
                    assignment.hidden = True
                if form.cleaned_data["shift_due_dates"]:
                    due = assignment.due
                    try:
                        assignment.due = due.replace(year=assignment.due.year + 1)
                    except ValueError:  # February 29 -> February 28
                        assignment.due = due + date(due.year + 1, 3, 1) - date(due.year, 3, 1)

                assignment.save()

                # Make directory with new ID
                assignment.make_assignment_dir()

                # Access the old assignment
                old_assignment = Assignment.objects.get(id=old_id)

                if form.cleaned_data["copy_graders"] and old_assignment.grader_file:
                    with open(old_assignment.grader_file.path, "r") as f:
                        assignment.save_grader_file(f.read())  # Save to new directory

                if form.cleaned_data["copy_files"]:
                    for _, filename, path, _, _ in old_assignment.list_files():
                        with open(path, "r") as f:
                            assignment.save_file(f.read(), filename)

            return redirect("courses:show", course.id)
    else:
        form = ImportFromSelectedCourseForm(course=other_course)

    return render(
        request,
        "courses/import_from_selected_course.html",
        {"form": form, "course": course, "nav_item": "Import"},
    )


@teacher_or_superuser_required
def students_view(request, course_id):
    """View students enrolled in a course"""
    course = get_object_or_404(Course.objects.filter_editable(request.user), id=course_id)

    period = request.GET.get("period", "all")
    period_set = course.period_set.order_by("teacher", "name")

    if period == "all":
        students = {s: course.period_set.filter(students=s) for s in course.students.all()}

        return render(
            request,
            "courses/students-all.html",
            {
                "nav_item": "Students",
                "course": course,
                "period": course.period_set.filter(students=request.user),
                "students": students,
                "period_set": period_set,
            },
        )
    else:
        active_period = get_object_or_404(Period.objects.filter(course=course), id=int(period))

        students = [
            [
                s,
                [
                    assignment.name
                    for assignment in Assignment.objects.filter_visible(request.user)
                    .filter(course=course)
                    .exclude(submissions__student=s)
                ],
            ]
            for s in active_period.students.all()
        ]

        return render(
            request,
            "courses/students.html",
            {
                "nav_item": "Students",
                "course": course,
                "period": course.period_set.filter(students=request.user),
                "students": students,
                "period_set": period_set,
                "active_period": active_period,
            },
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
            current_students = course.students.all()
            new_students = set(form.cleaned_data["students"])

            for student in (s for s in current_students if s not in new_students):
                for period in student.periods.filter(course=course):
                    period.students.remove(student)

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
            "nav_item": "Manage students",
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
