import datetime

from django.contrib import admin, messages
from django.utils.translation import ngettext

from .models import (
    Assignment,
    CooldownPeriod,
    FileAction,
    Folder,
    Language,
    MossResult,
    Quiz,
    QuizLogMessage,
    SubmissionCap,
)


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "assignments")
    list_filter = ("course",)
    ordering = ("course", "name")
    save_as = True
    search_fields = ("name",)
    autocomplete_fields = ("course",)

    @admin.display(description="Assignments")
    def assignments(self, obj):
        return len(obj.assignments.all())


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    date_hierarchy = "due"
    list_display = ("name", "course_name", "folder", "due", "visible", "quiz_icon")
    list_filter = ("language_details", "course", "due")
    ordering = ("-due",)
    save_as = True
    search_fields = ("name",)
    autocomplete_fields = ("course", "folder")

    @admin.display(description="Course")
    def course_name(self, obj):
        return obj.course.name

    @admin.display(description="Visible", boolean=True)
    def visible(self, obj):
        return not obj.hidden

    @admin.display(description="Quiz", boolean=True)
    def quiz_icon(self, obj):
        return bool(obj.is_quiz)


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("name", "language", "info", "is_deprecated")
    search_fields = ("name",)
    ordering = ("-language", "is_deprecated", "name")
    save_as = True
    list_filter = ("language",)
    actions = ["make_deprecated"]

    @admin.action(description="Mark languages as deprecated")
    def make_deprecated(self, request, queryset) -> None:
        changed = 0
        for language in queryset:
            language.is_deprecated = True
            language.name = f"{language.name} (Deprecated)"
            language.save()
            changed += 1

        self.message_user(
            request,
            ngettext(
                "Successfully marked %d language as deprecated.",
                "Successfully marked %d languages as deprecated.",
                changed,
            )
            % changed,
            messages.SUCCESS,
        )


@admin.register(CooldownPeriod)
class CooldownPeriodAdmin(admin.ModelAdmin):
    date_hierarchy = "start_time"
    list_display = ("id", "start_time", "end_time", "assignment", "student")
    list_filter = ("assignment__course",)
    ordering = ("-start_time",)
    save_as = True
    search_fields = ("assignment__name", "student__username")
    autocomplete_fields = ("assignment", "student")

    @admin.display(description="End Time")
    def end_time(self, obj):
        return obj.start_time + datetime.timedelta(minutes=obj.assignment.submission_limit_cooldown)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    date_hierarchy = "assignment__due"
    list_display = ("assignment", "course_name", "folder_name", "due", "action", "visible")
    list_filter = ("action",)
    ordering = ("-assignment__due",)
    save_as = True
    search_fields = ("assignment__name",)
    autocomplete_fields = ("assignment",)

    @admin.display(description="Due")
    def due(self, obj):
        return obj.assignment.due

    @admin.display(description="Course")
    def course_name(self, obj):
        return obj.assignment.course.name

    @admin.display(description="Folder")
    def folder_name(self, obj):
        return obj.assignment.folder.name if obj.assignment.folder else None

    @admin.display(description="Visible", boolean=True)
    def visible(self, obj):
        return not obj.assignment.hidden


@admin.register(QuizLogMessage)
class QuizLogMessageAdmin(admin.ModelAdmin):
    date_hierarchy = "date"
    list_display = ("content", "assignment", "student", "date", "severity")
    list_filter = ("student", "severity")
    ordering = ("-date",)
    save_as = True
    search_fields = ("assignment__name", "student__username", "content")
    autocomplete_fields = ("assignment", "student")


@admin.register(MossResult)
class MossResultAdmin(admin.ModelAdmin):
    date_hierarchy = "date"
    list_display = ("date", "assignment", "course_name", "language", "user_id", "status")
    list_filter = ("assignment__course", "language", "user_id")
    ordering = ("-date",)
    save_as = True
    search_fields = ("assignment__name", "url")
    autocomplete_fields = ("assignment",)

    @admin.display(description="Course")
    def course_name(self, obj):
        return obj.assignment.course.name


@admin.register(FileAction)
class FileActionAdmin(admin.ModelAdmin):
    list_display = ("name", "command", "match", "is_sandboxed")
    list_filter = ("is_sandboxed",)
    save_as = True
    search_fields = (
        "name",
        "match_value",
    )
    filter_horizontal = ("courses",)

    @admin.display(description="Match")
    def match(self, obj):
        if obj.match_type == "S":
            return f"{obj.match_value}*"
        elif obj.match_type == "E":
            return f"*{obj.match_value}"
        elif obj.match_type == "C":
            return f"*{obj.match_value}*"
        return ""


@admin.register(SubmissionCap)
class SubmissionCapAdmin(admin.ModelAdmin):
    list_display = ("assignment", "submission_cap", "submission_cap_after_due", "student")
    search_fields = ("assignment__name", "student__username")
    list_filter = ("assignment",)
    save_as = True
