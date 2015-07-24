from django.forms.models import inlineformset_factory
from utilities.forms import BaseTableFormSet
from .models import Letter, Attachment
from .forms import AttachmentForm

AttachmentFormSet = inlineformset_factory(
    Letter, Attachment, form=AttachmentForm, formset=BaseTableFormSet)
