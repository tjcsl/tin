from django.contrib import admin
from .models import User
from ..courses.models import StudentImportUser, StudentImport

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
