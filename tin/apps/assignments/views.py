from django.shortcuts import render

from .models import Assignment

# Create your views here.
def show_view(request, assignment_id):
    return render(request, "assignments/show.html", {"assignment": Assignment.objects.get(id = assignment_id)})

