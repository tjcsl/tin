from django import http
from django.shortcuts import render, redirect, get_object_or_404

from .models import Course
from .forms import CourseForm
from ..auth.decorators import login_required, teacher_or_superuser_required

# Create your views here.
@login_required
def index_view(request):
    if request.user.is_superuser:
        courses = Course.objects.all()
    elif request.user.is_teacher:
        courses = Course.objects.filter(teacher = request.user)
    else:
        courses = request.user.courses.all()

    return render(request, "courses/home.html", {"courses": courses})

@login_required
def show_view(request, course_id):
    try:
        course = Course.objects.get(id = course_id)
    except Course.DoesNotExist:
        pass
    else:
        if request.user.is_superuser or course in request.user.courses.all() or request.user == course.teacher:
            assignments = course.assignments.order_by("-due")
            return render(request, "courses/show.html", {"course": course, "assignments": assignments})
    raise http.Http404

@teacher_or_superuser_required
def create_view(request):
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit = True)
            course.teacher = request.user
            course.save()
            return redirect("auth:index")
    else:
        form = CourseForm()
    return render(request, "courses/edit_create.html", {"form": form, "action": "add"})

@teacher_or_superuser_required
def edit_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher and not request.user.is_superuser:
        return redirect("courses:index")

    if request.method == "POST":
        form = CourseForm(date=request.POST, instance=course)
        if form.is_valid():
            instance = form.save()
            return redirect("courses:index")
    else:
        form = CourseForm(instance=course)

    return render(request, "courses/edit_create.html", {"form": form, "course": course, "action": "edit"})
