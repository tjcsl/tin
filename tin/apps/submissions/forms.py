from django import forms
from django.db.models import Q

from .models import Submission, Comment
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
        return super().label_from_instance(obj)


class FilterForm(forms.Form):
    ORDER_CHOICES = (
        ("", "None"),
        ("date_submitted", "Oldest first"),
        ("-date_submitted", "Newest first"),
        ("assignment__name", "Assignment name, A to Z"),
        ("-assignment__name", "Assignment name, Z to A"),
        ("assignment__course__name", "Course name, A to Z"),
        ("-assignment__course__name", "Course name, Z to A"),
        ("assignment__folder__name", "Folder name, A to Z"),
        ("-assignment__folder__name", "Folder name, Z to A"),
        ("student__username", "Student username, A to Z"),
        ("-student__username", "Student username, Z to A"),
        ("student__last_name", "Student last name, A to Z"),
        ("-student__last_name", "Student last name, Z to A"),
        ("student__first_name", "Student first name, A to Z"),
        ("-student__first_name", "Student first name, Z to A"),
        ("points_received", "Points received, low to high"),
        ("-points_received", "Points received, high to low"),
        ("assignment__points_possible", "Points possible, low to high"),
        ("-assignment__points_possible", "Points possible, high to low"),
    )

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
    is_latest_publish = forms.BooleanField(label="Is latest or published?", required=False)
    is_latest = forms.BooleanField(label="Is latest?", required=False)
    is_published = forms.BooleanField(label="Is published?", required=False)
    has_been_graded = forms.BooleanField(label="Is graded?", required=False)
    has_not_been_graded = forms.BooleanField(label="Is not graded?", required=False)
    is_complete = forms.BooleanField(label="Is complete?", required=False)
    is_incomplete = forms.BooleanField(label="Is incomplete?", required=False)
    min_points = forms.IntegerField(label="Min points", required=False)
    max_points = forms.IntegerField(label="Max points", required=False)
    points_possible = forms.IntegerField(label="Total points possible", required=False)

    limit = forms.IntegerField(label="Limit", initial=1000, required=False)
    order_by_1 = forms.ChoiceField(
        label="Order by", choices=ORDER_CHOICES, required=False, initial=""
    )
    order_by_2 = forms.ChoiceField(
        label="Then by", choices=ORDER_CHOICES, required=False, initial=""
    )
    order_by_3 = forms.ChoiceField(
        label="Then by", choices=ORDER_CHOICES, required=False, initial=""
    )
    order_by_4 = forms.ChoiceField(
        label="Then by", choices=ORDER_CHOICES, required=False, initial=""
    )
    order_by_5 = forms.ChoiceField(
        label="Then by", choices=ORDER_CHOICES, required=False, initial=""
    )

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
            query = queryset.none()
            for period in self.cleaned_data["periods"]:
                query |= Q(student__in=period.students.all()) & Q(assignment__course=period.course)
            queryset = queryset.filter(query)

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

        order_bys = [self.cleaned_data[f"order_by_{i}"] for i in range(1, 6)]
        order_bys = filter(None, order_bys)  # Remove empty selections
        if order_bys:
            queryset = queryset.order_by(*order_bys)

        # This is done last to minimize queryset evaluation
        # However, slicing must be done last (see limit below)
        if self.cleaned_data["is_latest_publish"]:
            latest_publish_ids = [s.pk for s in queryset if (s.is_latest_publish or s.is_latest)]
            queryset = queryset.filter(pk__in=latest_publish_ids)

        if self.cleaned_data["is_latest"]:
            latest_ids = [s.pk for s in queryset if s.is_latest]
            queryset = queryset.filter(pk__in=latest_ids)

        if self.cleaned_data["is_published"]:
            published_ids = [s.pk for s in queryset if s.is_latest_publish]
            queryset = queryset.filter(pk__in=published_ids)

        if self.cleaned_data["limit"]:
            queryset = queryset[: self.cleaned_data["limit"]]

        return queryset


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text", "point_override"]
        widgets = {
            "text": forms.Textarea(attrs={"cols": 120, "rows": 5}),
            "point_override": forms.NumberInput(attrs={"step": 0.5}),
        }
