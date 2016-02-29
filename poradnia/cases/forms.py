# -*- coding: utf-8 -*-
import autocomplete_light.shortcuts as autocomplete_light
from atom.ext.crispy_forms.forms import FormHorizontalMixin, HelperMixin, SingleButtonMixin
from braces.forms import UserKwargModelFormMixin
from crispy_forms.layout import Submit
from django import forms
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import assign_perm

from .models import Case, PermissionGroup


class CaseForm(UserKwargModelFormMixin, FormHorizontalMixin, SingleButtonMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(CaseForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            self.helper.form_action = kwargs['instance'].get_edit_url()

    def save(self, commit=True, *args, **kwargs):
        obj = super(CaseForm, self).save(commit=False, *args, **kwargs)
        if obj.pk:  # old
            obj.modified_by = self.user
            verb, staff_only = (('closed', False)
                                if obj.status == Case.STATUS.closed
                                else ('updated', True))
            obj.send_notification(self.user, staff=staff_only, verb=verb)
        else:  # new
            obj.send_notification(self.user, staff=True, verb='created')
            obj.created_by = self.user
        if commit:
            obj.save()
        return obj

    class Meta:
        model = Case
        fields = ("name", "status")


class CaseGroupPermissionForm(HelperMixin, forms.Form):
    action_text = _('Grant')
    user = forms.ModelChoiceField(queryset=None,
                                  required=True,
                                  widget=autocomplete_light.ChoiceWidget('UserAutocomplete'),
                                  label=_("User"))
    group = forms.ModelChoiceField(queryset=PermissionGroup.objects.all(),
                                   label=_("Permissions group"))

    def __init__(self, user, case=None, *args, **kwargs):
        self.case = case
        self.user = user
        super(CaseGroupPermissionForm, self).__init__(*args, **kwargs)
        self.fields['user'].queryset = get_user_model().objects.for_user(self.user)
        self.helper.form_class = 'form-inline'
        self.helper.layout.append(Submit('grant', _('Grant')))

        self.helper.form_action = reverse('cases:permission_grant',
                                          kwargs={'pk': str(self.case.pk)})

    def assign(self):
        perms = [x.codename for x in self.cleaned_data['group'].permissions.all()]

        for perm in perms:
            assign_perm(perm, self.cleaned_data['user'], self.case)

        self.case.send_notification(actor=self.user,
                                    verb='grant_group',
                                    action_object=self.cleaned_data['user'],
                                    action_target=self.cleaned_data['group'],
                                    staff=True)
