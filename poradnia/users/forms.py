# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from guardian.forms import BaseObjectPermissionsForm
from guardian.shortcuts import assign_perm, remove_perm
from guardian.forms import UserObjectPermissionsForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from crispy_forms.bootstrap import FormActions
import autocomplete_light
from .models import User, Profile


class SaveButtonMixin(object):
    def __init__(self, *args, **kwargs):
        super(SaveButtonMixin, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout.append(
            FormActions(
                Submit('save_changes', _('Update'), css_class="btn-primary"),
                Submit('cancel', _('Cancel')),
            )
        )


class UserForm(SaveButtonMixin, forms.ModelForm):

    class Meta:
        # Set this form to use the User model.
        model = User

        # Constrain the UserForm to just these fields.
        fields = ("first_name", "last_name")


class ProfileForm(SaveButtonMixin, forms.ModelForm):
    helper = FormHelper()
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-lg-2'
    helper.field_class = 'col-lg-8'
    helper.layout = Layout(
        Field('description'),
        Field('www'),
    )

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


class SignupForm(forms.ModelForm):
    class Meta:
        model = get_user_model()  # use this function for swapping user model
        fields = ['first_name', 'last_name']

    def save(self, user):
        user.save()
