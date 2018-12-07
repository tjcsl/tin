from django import forms
from .models import Course
from ..users.models import User
from ..users.forms import UserMultipleChoiceField

class CourseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        self.fields["students"] = UserMultipleChoiceField(queryset = User.objects.filter(is_teacher = False).order_by("username"))

    class Meta:
        model = Course
        fields = ["name", "students"]

