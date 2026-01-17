from __future__ import annotations

from django import forms
from django.contrib import admin

from ..assignments.models import Language
from .models import Venv


class VenvAdminForm(forms.ModelForm):
    language = forms.ModelChoiceField(queryset=Language.objects.filter(language="P"))


@admin.register(Venv)
class VenvAdmin(admin.ModelAdmin):
    form = VenvAdminForm
    list_display = ("name", "fully_created", "installing_packages")
    list_filter = ("fully_created", "installing_packages")
    save_as = True
    search_fields = ("name",)
