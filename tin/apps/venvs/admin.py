from django.contrib import admin

from .models import Virtualenv

# Register your models here.


@admin.register(Virtualenv)
class VirtualenvAdmin(admin.ModelAdmin):
    list_display = ("assignment", "fully_created", "installing_packages")
    list_filter = ("fully_created", "installing_packages")
    save_as = True
    search_fields = ("assignment__name",)
    autocomplete_fields = ("assignment",)
