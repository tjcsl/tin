# -*- coding: utf-8 -*-
from django.shortcuts import render


def handle_404_view(request, exception):
    # Render it maybe?
    del exception
    return render(request, "error/404.html", status = 404)


def handle_500_view(request):
    return render(request, "error/500.html", status = 500)
