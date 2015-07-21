from django import forms
from utilities.forms import SaveButtonMixin, FormHorizontalMixin
from ..models import User, Profile


class UserForm(SaveButtonMixin, forms.ModelForm):
    class Meta:
        # Set this form to use the User model.
        model = User

        # Constrain the UserForm to just these fields.
        fields = ("first_name", "last_name")


class ProfileForm(FormHorizontalMixin, SaveButtonMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("description", "www")
