# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth import get_user_model
from guardian.forms import BaseObjectPermissionsForm
from guardian.shortcuts import get_users_with_perms
from guardian.shortcuts import assign_perm
from guardian.shortcuts import remove_perm
from .models import User


class UserForm(forms.ModelForm):

    class Meta:
        # Set this form to use the User model.
        model = User

        # Constrain the UserForm to just these fields.
        fields = ("first_name", "last_name")


class ManageObjectPermissionForm(BaseObjectPermissionsForm):
    users = forms.ModelMultipleChoiceField(queryset=get_user_model().objects.none(), required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.staff_only = kwargs.pop('staff_only', False)
        super(ManageObjectPermissionForm, self).__init__(*args, **kwargs)
        self.fields['users'].queryset = self.get_user_queryset()

    def get_user_queryset(self):
        qs = get_user_model().objects
        qs = qs.for_user(self.user)
        if self.staff_only:
            qs = qs.filter(is_staff=True)
        qs = qs.exclude(pk__in=[o.pk for o in get_users_with_perms(self.obj)])
        return qs

    def are_obj_perms_required(self):
        return True

    def save_obj_perms(self):
        for user in self.cleaned_data['user']:
            perms = self.cleaned_data[self.get_obj_perms_field_name()]
            model_perms = [c[0] for c in self.get_obj_perms_field_choices()]

            to_remove = set(model_perms) - set(perms)
            for perm in to_remove:
                remove_perm(perm, user, self.obj)

            for perm in perms:
                assign_perm(perm, user, self.obj)
