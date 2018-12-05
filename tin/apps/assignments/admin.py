from django.contrib import admin
from .models import Assignment

# Register your models here.

class AssignmentAdmin(admin.ModelAdmin):
    pass

admin.site.register(Assignment, AssignmentAdmin)
