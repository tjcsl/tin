from django import forms


class UserMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, user):  # pylint: disable=arguments-differ
        return "{} ({})".format(user.full_name, user.username)
