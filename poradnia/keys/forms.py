from braces.forms import UserKwargModelFormMixin
from django.forms import ModelForm

from atom.ext.crispy_forms.forms import SingleButtonMixin
from .models import Key


class KeyForm(UserKwargModelFormMixin, SingleButtonMixin, ModelForm):
    class Meta:
        model = Key
        fields = ['description', ]

    def save(self, commit=True, *args, **kwargs):
        obj = super(KeyForm, self).save(commit=False, *args, **kwargs)
        obj.user = self.user
        if commit:
            obj.save()
        return obj
