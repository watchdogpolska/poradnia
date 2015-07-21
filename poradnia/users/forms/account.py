# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Div
from crispy_forms.bootstrap import FormActions, PrependedText
from utilities.forms import FormHorizontalMixin


class SignupForm(FormHorizontalMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        self.helper = getattr(self, 'helper', FormHelper(self))
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.layout = Layout(
            Row(
                Div(
                    'first_name',
                    'last_name',
                    PrependedText('username', '<i class="fa fa-user"></i>'),
                    PrependedText('email', '@'),
                    PrependedText('password1', '<i class="fa fa-key"></i>', type='password'),
                    PrependedText('password2', '<i class="fa fa-key"></i>', type='password'),
                    FormActions(
                        Submit('signup', _('Signup'), css_class="btn-primary"),
                    ),
                    css_class='col-md-8 col-md-offset-2'
                )
            )
        )

    class Meta:
        model = get_user_model()  # use this function for swapping user model
        fields = ['first_name', 'last_name']

    def save(self, user):
        user.save()
