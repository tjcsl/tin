from django import forms

from ..assignments.models import Language
from .models import Venv


class VenvForm(forms.ModelForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["language"].queryset = Language.objects.filter(
            language="P", is_deprecated=False
        )

    class Meta:
        model = Venv
        fields = ["name", "language"]
        labels = {"language": "Python version"}
