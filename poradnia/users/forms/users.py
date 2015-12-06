from atom.ext.crispy_forms.forms import FormHorizontalMixin, SingleButtonMixin
from django import forms
from django.contrib.auth import get_user_model

from ..models import Profile


class UserForm(FormHorizontalMixin, SingleButtonMixin, forms.ModelForm):
    class Meta:
        # Set this form to use the User model.
        model = get_user_model()

        # Constrain the UserForm to just these fields.
        fields = ("first_name", "last_name", 'picture')


class ProfileForm(FormHorizontalMixin, SingleButtonMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("description", "www")
