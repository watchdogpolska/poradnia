# -*- coding: utf-8 -*-
from dal import autocomplete
from braces.forms import UserKwargModelFormMixin
from crispy_forms.layout import Submit
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import assign_perm

from atom.ext.crispy_forms.forms import (FormHorizontalMixin, HelperMixin,
                                         SingleButtonMixin)

from .models import Case, PermissionGroup

try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse


class CaseForm(UserKwargModelFormMixin, FormHorizontalMixin, SingleButtonMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CaseForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            self.helper.form_action = kwargs['instance'].get_edit_url()

    def save(self, commit=True, *args, **kwargs):
        obj = super(CaseForm, self).save(commit=False, *args, **kwargs)
        if obj.pk:  # old
            obj.modified_by = self.user
            if obj.status == Case.STATUS.assigned:
                obj.send_notification(self.user, staff=True, verb='updated')
        else:  # new
            obj.send_notification(self.user, staff=True, verb='created')
            obj.created_by = self.user
        if commit:
            obj.save()
        return obj

    class Meta:
        model = Case
        fields = ("name", "status", "has_project")


class CaseGroupPermissionForm(HelperMixin, forms.Form):
    action_text = _('Grant')
    user = forms.ModelChoiceField(queryset=None,
                                  required=True,
                                  widget=autocomplete.ModelSelect2('users:autocomplete'),
                                  label=_("User"))
    group = forms.ModelChoiceField(queryset=PermissionGroup.objects.all(),
                                   label=_("Permissions group"))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.case = kwargs.pop('case')
        super(CaseGroupPermissionForm, self).__init__(*args, **kwargs)
        self.fields['user'].queryset = get_user_model().objects.for_user(self.user)
        self.helper.form_class = 'form-inline'
        self.helper.layout.append(Submit('grant', _('Grant')))

        self.helper.form_action = reverse('cases:permission_grant',
                                          kwargs={'pk': str(self.case.pk)})

    def assign(self):
        for perm in self.cleaned_data['group'].permissions.all():
            assign_perm(perm, self.cleaned_data['user'], self.case)

        self.case.send_notification(actor=self.user,
                                    verb='grant_group',
                                    action_object=self.cleaned_data['user'],
                                    action_target=self.cleaned_data['group'],
                                    staff=True)


class CaseCloseForm(UserKwargModelFormMixin, HelperMixin, forms.ModelForm):
    notify = forms.BooleanField(required=False, label=_("Notify user"))

    def __init__(self, *args, **kwargs):
        super(CaseCloseForm, self).__init__(*args, **kwargs)
        self.helper.add_input(Submit('action', _('Close'), css_class="btn-primary"))

        if 'instance' in kwargs:
            self.helper.form_action = kwargs['instance'].get_close_url()

    def save(self, commit=True, *args, **kwargs):
        obj = super(CaseCloseForm, self).save(commit=False, *args, **kwargs)
        obj.modified_by = self.user
        obj.status = Case.STATUS.closed
        if self.cleaned_data['notify']:
            obj.send_notification(self.user, staff=False, verb='closed')
        if commit:
            obj.save()
        return obj

    class Meta:
        model = Case
        fields = ()
