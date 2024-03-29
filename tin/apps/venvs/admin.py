from django.contrib import admin

from .models import Venv

# Register your models here.


@admin.register(Venv)
class VenvAdmin(admin.ModelAdmin):
    list_display = ("name", "fully_created", "installing_packages")
    list_filter = ("fully_created", "installing_packages")
    save_as = True
    search_fields = ("name",)
