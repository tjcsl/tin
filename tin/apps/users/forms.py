from __future__ import annotations

from django import forms


class UserMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, user):  # pylint: disable=arguments-differ
        return f"{user.full_name} ({user.username})"


class ThemeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["dark_mode"]
