# -*- coding: utf-8 -*-
from django import forms
from crispy_forms.helper import FormHelper


from .models import Case


class CaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.helper = FormHelper()
        self.helper.form_tag = False
        if 'instance' in kwargs:
            self.helper.form_action = kwargs['instance'].get_edit_url()
        super(CaseForm, self).__init__(*args, **kwargs)

    def save(self, commit=True, *args, **kwargs):
        obj = super(CaseForm, self).save(commit=False, *args, **kwargs)
        if obj.pk:  # update
            obj.modified_by = self.user
            obj.send_notification(self.user, 'updated')
        else:  # new
            obj.send_notification(self.user, 'created')
            obj.created_by = self.user
        if commit:
            obj.save()
        return obj

    class Meta:
        # Set this form to use the User model.
        model = Case
        fields = ("name", "status", "tags")
