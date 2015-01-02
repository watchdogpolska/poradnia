# -*- coding: utf-8 -*-
from django import forms

from .models import Case


class CaseForm(forms.ModelForm):

    class Meta:
        # Set this form to use the User model.
        model = Case
        fields = ("name", "status")
