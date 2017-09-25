from atom.ext.crispy_forms.forms import (FormHorizontalMixin, HelperMixin,
                                         SingleButtonMixin)
from atom.forms import AuthorMixin
from braces.forms import UserKwargModelFormMixin
from crispy_forms.layout import Fieldset, Layout
from django import forms
from django.forms import ModelForm
from django.utils.timezone import now
from django.utils.translation import ugettext as _

from poradnia.cases.models import Case
from .models import Advice, Attachment


class AdviceForm(UserKwargModelFormMixin, FormHorizontalMixin, SingleButtonMixin,
                 AuthorMixin, ModelForm):
    def __init__(self, *args, **kwargs):
        super(AdviceForm, self).__init__(*args, **kwargs)
        self.helper.form_method = 'post'
        self.fields['advicer'].initial = self.user
        self.fields['grant_on'].initial = now()
        self.fields['case'].queryset = Case.objects.for_user(self.user).all()
        self.fields['case'].help_text = _('Select from poradnia.cases which do '
                                          'you have a permission')
        self.helper.layout = Layout(
            Fieldset(
                _('Statistic data'),
                'case',
                'issues',
                'area',
                'person_kind',
                'institution_kind',
                'helped'
            ),
            Fieldset(
                _('Details'),
                'subject',
                'grant_on',
                'advicer',
                'comment',
            ),
        )

    class Meta:
        model = Advice
        fields = ['case', 'subject', 'grant_on', 'issues', 'area',
                  'person_kind', 'institution_kind', 'advicer', 'comment', 'helped']


class AttachmentForm(HelperMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AttachmentForm, self).__init__(*args, **kwargs)
        self.helper.form_tag = False
        self.helper.form_method = 'post'

    class Meta:
        model = Attachment
        fields = ['attachment']
