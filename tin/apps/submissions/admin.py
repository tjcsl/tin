from django.contrib import admin

from .models import Submission

# Register your models here.


class SubmissionAdmin(admin.ModelAdmin):
    pass


admin.site.register(Submission, SubmissionAdmin)
