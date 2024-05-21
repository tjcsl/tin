from __future__ import annotations

from django.contrib import admin

from .models import User

# Register your models here.


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    date_hierarchy = "date_joined"
    list_display = (
        "username",
        "full_name",
        "email",
        "is_student",
        "is_teacher",
        "is_staff",
        "is_superuser",
    )
    list_filter = (
        "date_joined",
        "last_login",
        "is_student",
        "is_teacher",
        "is_staff",
        "is_superuser",
    )
    ordering = ("username",)
    save_as = True
    search_fields = ("username", "full_name")
