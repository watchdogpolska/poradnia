from django.forms.models import inlineformset_factory
from utilities.forms import BaseTableFormSet
from .models import Letter, Attachment



def formset_attachment_factory(form_formset=BaseTableFormSet, parent_cls=Letter, inline_cls=Attachment, *args, **kwargs):
    from .forms import AttachmentForm
    return inlineformset_factory(parent_cls, inline_cls, form=AttachmentForm, formset=form_formset,
        *args, **kwargs)
