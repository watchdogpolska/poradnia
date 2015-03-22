from django.forms.models import BaseInlineFormSet
from django.forms.models import inlineformset_factory
from crispy_forms.helper import FormHelper
from .models import Letter, Attachment


class FormsetHelper(FormHelper):
    form_tag = False
    form_method = 'post'


class TableInlineHelper(FormsetHelper):
    template = 'bootstrap/table_inline_formset.html'


def formset_attachment_factory(form_formset=None, *args, **kwargs):
    from .forms import AttachmentForm
    if form_formset is None:
        class BaseAttachmentFormSet(BaseInlineFormSet):
            helper = TableInlineHelper()
        form_formset = BaseAttachmentFormSet
    return inlineformset_factory(Letter, Attachment, form=AttachmentForm, formset=form_formset,
        *args, **kwargs)
