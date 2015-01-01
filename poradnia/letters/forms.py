from django.forms import ModelForm
from .models import Letter, Attachment
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib.auth import get_user_model
from cases.models import Case


class LetterForm(ModelForm):
    client = forms.ModelChoiceField(queryset=get_user_model().objects.all())

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = ''
        self.helper.add_input(Submit('submit', 'Submit'))
        super(LetterForm, self).__init__(*args, **kwargs)
        if not self.user.has_perm('cases.can_select_client'):
            del self.fields['client']
        else:
            self.fields['client'].initial = self.user

    def save(self, case_id=None, commit=True, *args, **kwargs):
        obj = super(LetterForm, self).save(commit=False, *args, **kwargs)
        if 'client' in self.cleaned_data and self.cleaned_data['client']:
            client = self.cleaned_data['client']
        else:
            client = self.user

        if case_id:
            case = Case.objects.get_or_create(case_id=case_id)
        else:
            case = Case(name=self.cleaned_data['name'], client=client)
            case.save()
        obj.case = case
        obj.created_by = self.user
        if commit:
            obj.save()
        return obj

    class Meta:
        fields = ['name', 'text']
        model = Letter


"""
class AttachmentForm(ModelForm)
    class Meta:
        fields = ['attachment', 'text']
        model = Attachment
"""
