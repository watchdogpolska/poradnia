from datetime import datetime
from django.forms import ModelForm
from braces.forms import UserKwargModelFormMixin
from crispy_forms.helper import FormHelper
from .models import Advice


class AdviceForm(UserKwargModelFormMixin, ModelForm):
    def __init__(self, *args, **kwargs):
        super(AdviceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_method = 'post'
        self.fields['advicer'].initial = self.user
        self.fields['grant_on'].initial = datetime.now()

    class Meta:
        model = Advice
        fields = ['subject', 'grant_on', 'issues', 'area',
            'person_kind', 'institution_kind', 'advicer', 'comment']

    def save(self, commit=True, *args, **kwargs):
        obj = super(AdviceForm, self).save(commit=False, *args, **kwargs)
        obj.created_by = self.user
        obj.modified_by = self.user
        if commit:
            obj.save()
        return obj
