# -*- coding: utf-8 -*-
from django import forms
from crispy_forms.helper import FormHelper
from letters.forms import PartialMixin
from django.core.urlresolvers import reverse

from .models import Event


class EventForm(PartialMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.case = kwargs.pop('case')
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_action = reverse('events:add', kwargs={'case_pk': self.case.pk})
        if 'instance' in kwargs:
            self.helper.form_action = kwargs['instance'].get_edit_url()
        super(EventForm, self).__init__(*args, **kwargs)

    def save(self, commit=True, *args, **kwargs):
        obj = super(EventForm, self).save(commit=False, *args, **kwargs)
        created = False if obj.pk else True
        obj.case = self.case
        if created:
            obj.created_by = self.user
        else:
            obj.modified_by = self.user
        obj.save()
        obj.send_notification(self.user, 'created' if created else 'updated')
        return obj

    class Meta:
        # Set this form to use the User model.
        model = Event
        fields = ("deadline", "time", "for_client", "text")
