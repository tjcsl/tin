from django import forms

from .models import Submission
from ..assignments.models import Folder, Assignment
from ..courses.models import Course, Period
from ..users.forms import UserMultipleChoiceField
from ..users.models import User


class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        if isinstance(obj, Course):
            return obj.name
        elif isinstance(obj, Folder):
            return f"{obj.name} (in {obj.course.name})"
        elif isinstance(obj, Assignment):
            if obj.folder:
                return f"{obj.name} (in {obj.folder.name} in {obj.course.name})"
            return f"{obj.name} (in {obj.course.name})"
        elif isinstance(obj, Period):
            return f"{obj.name} (in {obj.course.name})"


class FilterForm(forms.Form):
    courses = CustomModelMultipleChoiceField(
        label="Courses", queryset=Course.objects.all().order_by("name"), required=False
    )
    folders = CustomModelMultipleChoiceField(
        label="Folders", queryset=Folder.objects.all().order_by("name"), required=False
    )
    assignments = CustomModelMultipleChoiceField(
        label="Assignments", queryset=Assignment.objects.all().order_by("name"), required=False
    )
    periods = CustomModelMultipleChoiceField(
        label="Periods", queryset=Period.objects.all().order_by("name"), required=False
    )
    students = UserMultipleChoiceField(
        label="Students",
        queryset=User.objects.filter(is_student=True).order_by("last_name", "first_name"),
        required=False,
    )
    start_date = forms.DateTimeField(label="From", required=False)
    end_date = forms.DateTimeField(label="To", required=False)
    has_been_graded = forms.BooleanField(label="Is graded?", required=False)
    has_not_been_graded = forms.BooleanField(label="Is not graded?", required=False)
    is_complete = forms.BooleanField(label="Is complete?", required=False)
    is_incomplete = forms.BooleanField(label="Is incomplete?", required=False)
    min_points = forms.IntegerField(label="Min points", required=False)
    max_points = forms.IntegerField(label="Max points", required=False)
    points_possible = forms.IntegerField(label="Points possible", required=False)

    def get_results(self):
        """Returns a queryset of submissions matching the form's filters"""
        queryset = Submission.objects.all()

        if self.cleaned_data["courses"]:
            queryset = queryset.filter(assignment__course__in=self.cleaned_data["courses"])

        if self.cleaned_data["folders"]:
            queryset = queryset.filter(assignment__folder__in=self.cleaned_data["folders"])

        if self.cleaned_data["assignments"]:
            queryset = queryset.filter(assignment__in=self.cleaned_data["assignments"])

        if self.cleaned_data["periods"]:
            students_in_periods = Period.objects.none()
            for period in self.cleaned_data["periods"]:
                students_in_periods |= period.students.all()
            queryset = queryset.filter(student__in=students_in_periods)

        if self.cleaned_data["students"]:
            queryset = queryset.filter(student__in=self.cleaned_data["students"])

        if self.cleaned_data["start_date"]:
            queryset = queryset.filter(date_submitted__gte=self.cleaned_data["start_date"])

        if self.cleaned_data["end_date"]:
            queryset = queryset.filter(date_submitted__lte=self.cleaned_data["end_date"])

        if self.cleaned_data["has_been_graded"]:
            queryset = queryset.filter(has_been_graded=True)

        if self.cleaned_data["has_not_been_graded"]:
            queryset = queryset.filter(has_been_graded=False)

        if self.cleaned_data["is_complete"]:
            queryset = queryset.filter(complete=True)

        if self.cleaned_data["is_incomplete"]:
            queryset = queryset.filter(complete=False)

        if self.cleaned_data["min_points"]:
            queryset = queryset.filter(points_received__gte=self.cleaned_data["min_points"])

        if self.cleaned_data["max_points"]:
            queryset = queryset.filter(points_received__lte=self.cleaned_data["max_points"])

        if self.cleaned_data["points_possible"]:
            queryset = queryset.filter(
                assignment__points_possible=self.cleaned_data["points_possible"]
            )

        return queryset
