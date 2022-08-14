from django import forms

from ..users.forms import UserMultipleChoiceField
from ..users.models import User
from .models import Course, Period


class CourseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        self.fields["teacher"] = UserMultipleChoiceField(
            queryset=User.objects.filter(is_teacher=True).order_by("last_name", "first_name"),
            required=True,
        )

    class Meta:
        model = Course
        fields = ["name", "teacher", "sort_assignments_by"]


class StudentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        self.fields["students"] = UserMultipleChoiceField(
            queryset=User.objects.order_by("last_name", "first_name"),
            required=True,
        )

    class Meta:
        model = Course
        fields = ["students"]


class PeriodForm(forms.ModelForm):
    def __init__(self, course, *args, **kwargs):
        super(PeriodForm, self).__init__(*args, **kwargs)
        self.fields["teacher"] = forms.ModelChoiceField(
            queryset=course.teacher.order_by("last_name", "first_name"),
            required=True,
        )
        self.fields["students"] = UserMultipleChoiceField(
            queryset=course.students.order_by("last_name", "first_name"),
            required=False,
        )

    class Meta:
        model = Period
        fields = ["name", "teacher", "students"]
