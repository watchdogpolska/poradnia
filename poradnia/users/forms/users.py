from django import forms
from django.contrib.auth import get_user_model
from atom.ext.crispy_forms.forms import FormHorizontalMixin, SingleButtonMixin

from ..models import Profile


class UserForm(FormHorizontalMixin, SingleButtonMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        if (not self.instance or
                self.instance and not self.instance.is_staff):
            del self.fields['codename']

    class Meta:
        # Set this form to use the User model.
        model = get_user_model()

        # Constrain the UserForm to just these fields.
        fields = ("first_name", "last_name", 'picture', 'codename')


class ProfileForm(FormHorizontalMixin, SingleButtonMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("description", "www")
