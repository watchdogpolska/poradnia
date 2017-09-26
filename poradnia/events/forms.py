# -*- coding: utf-8 -*-
from django import forms

from atom.ext.crispy_forms.forms import FormHorizontalMixin, SingleButtonMixin
from atom.forms import AuthorMixin
from poradnia.letters.forms import PartialMixin
from .models import Event

try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse


class EventForm(PartialMixin, AuthorMixin, FormHorizontalMixin, SingleButtonMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.case = kwargs.pop('case')
        super(EventForm, self).__init__(*args, **kwargs)
        self.helper.form_action = reverse('events:add', kwargs={'case_pk': self.case.pk})
        if kwargs.get('instance', False):
            self.helper.form_action = kwargs['instance'].get_edit_url()

    def save(self, commit=True, *args, **kwargs):
        obj = super(EventForm, self).save(commit=False, *args, **kwargs)
        created = obj.pk is None
        obj.case = self.case
        obj.save()
        obj.send_notification(actor=self.user, staff=True, verb='created' if created else 'updated')
        return obj

    class Meta:
        # Set this form to use the User model.
        model = Event
        fields = ("deadline", "time", "text")
