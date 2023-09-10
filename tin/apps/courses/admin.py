from django.contrib import admin

from .models import Course, Period, StudentImportUser, StudentImport


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "teachers")
    ordering = ("name",)
    save_as = True
    search_fields = ("name", "teacher__username")
    filter_horizontal = ("teacher", "students")

    @admin.display(description="Teachers")
    def teachers(self, obj):
        return obj.get_teacher_str()


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ("name", "course_name", "teacher")
    list_filter = ("course", "teacher")
    ordering = ("course__name", "teacher__username", "name")
    save_as = True
    search_fields = ("name", "course__name", "teacher__username")
    autocomplete_fields = ("course", "teacher")
    filter_horizontal = ("students",)

    @admin.display(description="Course")
    def course_name(self, obj):
        return obj.course.name


@admin.register(StudentImportUser)
class StudentImportUserAdmin(admin.ModelAdmin):
    list_display = ("user",)
    ordering = ("user",)
    save_as = True
    search_fields = ("user",)


@admin.register(StudentImport)
class StudentImportAdmin(admin.ModelAdmin):
    list_display = ("course_name", "student_count")
    ordering = ("course__name",)
    save_as = True
    search_fields = ("course__name", "students__user")
    autocomplete_fields = ("course",)
    filter_horizontal = ("students",)

    @admin.display(description="Course")
    def course_name(self, obj):
        return obj.course.name

    @admin.display(description="Students")
    def student_count(self, obj):
        return len(obj.students.all())
