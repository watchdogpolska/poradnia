from django.forms.models import inlineformset_factory
from atom.forms import BaseTableFormSet
from .models import Letter, Attachment
from .forms import AttachmentForm

AttachmentFormSet = inlineformset_factory(
    Letter, Attachment, fields=('id', 'attachment'), form=AttachmentForm, formset=BaseTableFormSet)
