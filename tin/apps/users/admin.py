from django.contrib import admin

from ..courses.models import StudentImport, StudentImportUser
from .models import User

# Register your models here.


class UserAdmin(admin.ModelAdmin):
    pass


class StudentImportAdmin(admin.ModelAdmin):
    pass


class StudentImportUserAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)
admin.site.register(StudentImport, StudentImportAdmin)
admin.site.register(StudentImportUser, StudentImportUserAdmin)
