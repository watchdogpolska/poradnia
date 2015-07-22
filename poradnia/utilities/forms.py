from functools import partial
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Reset
from crispy_forms.bootstrap import FormActions
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l
from multiupload.fields import MultiFileField


class HelperMixin(object):
    form_helper_cls = FormHelper

    def __init__(self, *args, **kwargs):
        super(HelperMixin, self).__init__(*args, **kwargs)
        self.helper = getattr(self, 'helper', self.form_helper_cls(self))


class SingleButtonMixin(HelperMixin):
    action_text = _l('Save')
    form_helper_cls = FormHelper

    def __init__(self, *args, **kwargs):
        super(SingleButtonMixin, self).__init__(*args, **kwargs)
        self.helper.layout.append(
            FormActions(
                Submit('action', self.action_text, css_class="btn-primary"),
            )
        )


class SaveButtonMixin(HelperMixin):
    def __init__(self, *args, **kwargs):
        super(SaveButtonMixin, self).__init__(*args, **kwargs)
        self.helper.layout.append(
            FormActions(
                Submit('save_changes', _('Update'), css_class="btn-primary"),
                Reset('reset', _('Reset!'))
,
            )
        )


class FormHorizontalMixin(HelperMixin):
    def __init__(self, *args, **kwargs):
        super(FormHorizontalMixin, self).__init__(*args, **kwargs)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'


class FileMixin(forms.Form):  # TODO: Generalize
    files = MultiFileField(label=_("Attachments"), required=False)
    attachment_cls = None
    attachment_rel_field = None
    attachment_file_field = None

    def save(self, commit=True, *args, **kwargs):
        obj = super(FileMixin, self).save(commit=False, *args, **kwargs)
        attachments = []
        for each in self.cleaned_data['files']:
            kw = {self.attachment_rel_field: each, self.attachment_file_field: obj}
            attachments.append(self.attachment_cls(**kw))
        self.attachment_cls.objects.bulk_create(attachments)
        return obj


class PartialMixin(object):
    @classmethod
    def partial(cls, *args, **kwargs):
        return partial(cls, *args, **kwargs)


class AuthorMixin(object):
    def save(self, commit=True, *args, **kwargs):
        obj = super(AuthorMixin, self).save(commit=False, *args, **kwargs)
        if obj.pk:  # update
            obj.modified_by = self.user
        else:  # new
            obj.created_by = self.user
        if commit:
            obj.save()
        return obj
