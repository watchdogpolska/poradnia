from braces.forms import UserKwargModelFormMixin
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


class ProfileForm(UserKwargModelFormMixin, FormHorizontalMixin, SingleButtonMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        # dynamically exclude event_reminder_time if user is not a staff member
        if not self.user.is_staff:
            del self.fields['event_reminder_time']

    class Meta:
        model = Profile
        fields = ("description", "www", "event_reminder_time")
