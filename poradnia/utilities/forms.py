from functools import partial
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.bootstrap import FormActions
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l
from multiupload.fields import MultiFileField


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


class FileMixin(forms.Form):  # TODO: Generalize
    files = MultiFileField(label=_("Attachments"))
    attachment_cls = None

    def save(self, commit=True, *args, **kwargs):
        obj = super(FileMixin, self).save(commit=False, *args, **kwargs)
        attachments = []
        for each in self.cleaned_data['files']:
            attachments.append(self.attachment_cls(file=each, letter=obj))
        self.attachment_cls.objects.bulk_create(attachments)
        return obj


class PartialMixin(object):
    @classmethod
    def partial(cls, *args, **kwargs):
        return partial(cls, *args, **kwargs)
