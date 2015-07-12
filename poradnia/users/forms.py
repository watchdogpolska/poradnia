# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l
from guardian.forms import BaseObjectPermissionsForm
from guardian.shortcuts import assign_perm, remove_perm
from guardian.forms import UserObjectPermissionsForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Div
from crispy_forms.bootstrap import FormActions, PrependedText
import autocomplete_light
from .models import User, Profile


class SingleButtonMixin(object):
    action_text = _l('Save')

    def __init__(self, *args, **kwargs):
        super(SingleButtonMixin, self).__init__(*args, **kwargs)
        self.helper = getattr(self, 'helper', FormHelper(self))
        self.helper.layout.append(
            FormActions(
                Submit('action', self.action_text, css_class="btn-primary"),
            )
        )


class SaveButtonMixin(object):
    def __init__(self, *args, **kwargs):
        super(SaveButtonMixin, self).__init__(*args, **kwargs)
        self.helper = getattr(self, 'helper', FormHelper(self))
        self.helper.layout.append(
            FormActions(
                Submit('save_changes', _('Update'), css_class="btn-primary"),
                Submit('cancel', _('Cancel')),
            )
        )


class FormHorizontalMixin(object):
    def __init__(self, *args, **kwargs):
        super(FormHorizontalMixin, self).__init__(*args, **kwargs)
        self.helper = getattr(self, 'helper', FormHelper(self))
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'


class UserForm(FormHorizontalMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.helper.layout = Layout(
            PrependedText('first_name', 'A'),
            PrependedText('last_name', 'B'),
            FormActions(
                Submit('save_changes', _('Update'), css_class="btn-primary"),
                Submit('cancel', _('Cancel')),
            )
        )

    class Meta:
        # Set this form to use the User model.
        model = User

        # Constrain the UserForm to just these fields.
        fields = ("first_name", "last_name")


class ProfileForm(FormHorizontalMixin,SaveButtonMixin, forms.ModelForm):

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


class SignupForm(FormHorizontalMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        self.helper = getattr(self, 'helper', FormHelper(self))
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.layout = Layout(
            Row(
                Div(PrependedText('first_name', 'A'), css_class='col-md-6'),
                Div(PrependedText('last_name', 'B'), css_class='col-md-6')
            ),
            PrependedText('username', '<i class="fa fa-user"></i>'),
            PrependedText('email', '@'),
            Row(
                Div(PrependedText('password1', '<i class="fa fa-key"></i>', type='password'),
                    css_class='col-md-6'),
                Div(PrependedText('password2', '<i class="fa fa-key"></i>', type='password'),
                    css_class='col-md-6'),
            ),
            FormActions(
                Submit('signup', _('Signup'), css_class="btn-primary"),
            )
        )

    class Meta:
        model = get_user_model()  # use this function for swapping user model
        fields = ['first_name', 'last_name']

    def save(self, user):
        user.save()


from allauth.account.forms import LoginForm


class CustomLoginForm(SingleButtonMixin, LoginForm):
    action_text = _l('Sign In')
    pass
