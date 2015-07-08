# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from guardian.forms import BaseObjectPermissionsForm
from guardian.shortcuts import get_users_with_perms
from guardian.shortcuts import assign_perm
from guardian.shortcuts import remove_perm
import autocomplete_light
from .models import User, Profile
from guardian.forms import UserObjectPermissionsForm


class UserForm(forms.ModelForm):

    class Meta:
        # Set this form to use the User model.
        model = User

        # Constrain the UserForm to just these fields.
        fields = ("first_name", "last_name")


class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ("description", "www")


class PermissionsTranslationMixin(object):
    def __init__(self, *args, **kwargs):
        super(PermissionsTranslationMixin, self).__init__(*args, **kwargs)
        self.fields['permissions'].choices = [(key, _(value)) for key, value in self.fields['permissions'].choices]


class TranslatedUserObjectPermissionsForm(PermissionsTranslationMixin, UserObjectPermissionsForm):
    pass


class TranslatedManageObjectPermissionForm(PermissionsTranslationMixin, BaseObjectPermissionsForm):
    users = forms.ModelMultipleChoiceField(queryset=get_user_model().objects.none(), required=True,
        widget=autocomplete_light.MultipleChoiceWidget('UserAutocomplete'))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.staff_only = kwargs.pop('staff_only', False)
        super(TranslatedManageObjectPermissionForm, self).__init__(*args, **kwargs)
        # Update queryset dynamically
        self.fields['users'].queryset = get_user_model().objects.for_user(self.user).all()

    def are_obj_perms_required(self):
        return True

    def save_obj_perms(self):
        for user in self.cleaned_data['users']:
            perms = self.cleaned_data[self.get_obj_perms_field_name()]
            model_perms = [c[0] for c in self.get_obj_perms_field_choices()]

            to_remove = set(model_perms) - set(perms)
            for perm in to_remove:
                remove_perm(perm, user, self.obj)

            for perm in perms:
                assign_perm(perm, user, self.obj)
