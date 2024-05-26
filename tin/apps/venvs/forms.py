from __future__ import annotations

from django import forms

from .models import Venv


class VenvForm(forms.ModelForm):
    class Meta:
        model = Venv
        fields = ["name"]
