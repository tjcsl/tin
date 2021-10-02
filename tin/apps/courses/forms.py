from django import forms

from ..users.forms import UserMultipleChoiceField
from ..users.models import User
from .models import Course, Period


class CourseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        self.fields["students"] = UserMultipleChoiceField(
            queryset=User.objects.filter(is_teacher=False).order_by("last_name", "first_name"),
            required=False,
        )

    class Meta:
        model = Course
        fields = ["name", "students"]

class PeriodForm(forms.ModelForm):
    def __init__(self, course, *args, **kwargs):
        super(PeriodForm, self).__init__(*args, **kwargs)
        self.fields["students"] = UserMultipleChoiceField(
            queryset=course.students.order_by("last_name", "first_name"),
            required=False,
        )

    class Meta:
        model = Period
        fields = ["name", "students"]
