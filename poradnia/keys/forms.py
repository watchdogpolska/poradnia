from django.forms import ModelForm
from braces.forms import UserKwargModelFormMixin
from utilities.forms import SaveButtonMixin
from .models import Key


class KeyForm(UserKwargModelFormMixin, SaveButtonMixin, ModelForm):
    class Meta:
        model = Key
        fields = ['description', ]

    def save(self, commit=True, *args, **kwargs):
        obj = super(KeyForm, self).save(commit=False, *args, **kwargs)
        obj.user = self.user
        if commit:
            obj.save()
        return obj
