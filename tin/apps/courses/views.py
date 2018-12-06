from django import http
from django.shortcuts import render

from .models import Course
from ..auth.decorators import login_required

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
        if course in request.user.courses.all() or request.user == course.teacher:
            return render(request, "courses/show.html", {"course": course})
    raise http.Http404

