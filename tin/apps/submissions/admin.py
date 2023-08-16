from django.contrib import admin

from .models import Submission, Comment

# Register your models here.


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    date_hierarchy = "date_submitted"
    list_display = (
        "id",
        "assignment_name",
        "student_name",
        "date_submitted",
        "complete",
        "has_been_graded",
        "points_received",
        "kill_requested",
    )
    list_filter = ("assignment__course", "assignment__due")
    ordering = ("-date_submitted",)
    save_as = True
    search_fields = ("assignment__name", "student__username")

    @admin.display(description="Assignment")
    def assignment_name(self, obj):
        return obj.assignment.name

    @admin.display(description="Student")
    def student_name(self, obj):
        return obj.student.username


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    date_hierarchy = "date"
    list_display = (
        "submission",
        "author",
        "date",
        "point_override",
    )
    list_filter = ("submission__assignment__course", "submission__assignment__due")
    ordering = ("-date",)
    save_as = True
    search_fields = ("submission__assignment__name", "submission__student__username")

    @admin.display(description="Submission")
    def submission(self, obj):
        return obj.submission.id

    @admin.display(description="Author")
    def author(self, obj):
        return obj.author.username
