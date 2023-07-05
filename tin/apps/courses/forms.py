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


class SelectCourseToImportFromForm(forms.Form):
    def __init__(self, courses, *args, **kwargs):
        super(SelectCourseToImportFromForm, self).__init__(*args, **kwargs)
        self.fields["course"] = forms.ModelChoiceField(
            label="Course to Import From", widget=forms.RadioSelect, queryset=courses
        )


class ImportFromSelectedCourseForm(forms.Form):
    def __init__(self, course, *args, **kwargs):
        super(ImportFromSelectedCourseForm, self).__init__(*args, **kwargs)
        self.fields["folders"] = forms.ModelMultipleChoiceField(
            label="Select Folders",
            widget=forms.CheckboxSelectMultiple,
            queryset=course.folders.order_by("name"),
            required=False,
        )
        self.fields["assignments"] = forms.ModelMultipleChoiceField(
            label="Select Other Assignments",
            widget=forms.CheckboxSelectMultiple,
            queryset=course.assignments.filter(folder=None).order_by("name"),
            required=False,
        )
        self.fields["hide"] = forms.BooleanField(
            label="Hide?",
            required=False,
            help_text="Sets all imported assignments as hidden from students.",
        )
        self.fields["shift_due_dates"] = forms.BooleanField(
            label="Shift due date?",
            required=False,
            help_text="Shifts imported assignment due dates by one year.",
        )
        self.fields["copy_graders"] = forms.BooleanField(
            label="Copy graders?",
            required=False,
            help_text="Also imports any assignment grader scripts.",
        )
        self.fields["copy_files"] = forms.BooleanField(
            label="Copy files?",
            required=False,
            help_text="Also imports any uploaded files.",
        )


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
