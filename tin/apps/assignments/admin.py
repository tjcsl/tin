from django.contrib import admin

from .models import Assignment, LogMessage, Quiz


class AssignmentAdmin(admin.ModelAdmin):
    pass


admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(LogMessage)
admin.site.register(Quiz)
