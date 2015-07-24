from datetime import datetime
from django.utils.translation import ugettext as _
from django import forms
from braces.forms import UserKwargModelFormMixin
import autocomplete_light
from cases.models import Case
from utilities.forms import FormHorizontalMixin, SingleButtonMixin, AuthorMixin, HelperMixin
from .models import Advice, Attachment


class AdviceForm(UserKwargModelFormMixin, FormHorizontalMixin, SingleButtonMixin, AuthorMixin,
        autocomplete_light.ModelForm):

    def __init__(self, *args, **kwargs):
        super(AdviceForm, self).__init__(*args, **kwargs)
        self.helper.form_method = 'post'
        self.fields['advicer'].initial = self.user
        self.fields['grant_on'].initial = datetime.now()
        self.fields['case'].queryset = Case.objects.for_user(self.user).all()
        self.fields['case'].help_text = _('Select from cases which do you have a permission')

    class Meta:
        model = Advice
        fields = ['case', 'subject', 'grant_on', 'issues', 'area',
            'person_kind', 'institution_kind', 'advicer', 'comment']


class AttachmentForm(HelperMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AttachmentForm, self).__init__(*args, **kwargs)
        self.helper.form_tag = False
        self.helper.form_method = 'post'

    class Meta:
        model = Attachment
        fields = ['attachment']
