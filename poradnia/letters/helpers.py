from django.forms.models import inlineformset_factory

from atom.forms import BaseTableFormSet

from .forms import AttachmentForm
from .models import Attachment, Letter

AttachmentFormSet = inlineformset_factory(
    Letter, Attachment, fields=('id', 'attachment'), form=AttachmentForm, formset=BaseTableFormSet)
