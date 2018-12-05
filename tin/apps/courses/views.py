from django.shortcuts import render

from .models import Course

# Create your views here.
def index_view(request):
    return render(request, "courses/home.html")

def show_view(request, course_id):
    return render(request, "courses/show.html", {"course": Course.objects.get(id = course_id)})

