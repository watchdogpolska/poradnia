from django.forms import ModelForm
from .models import Letter, Attachment


class LetterForm(ModelForm):
    class Meta:
        fields = ['text']
        model = Letter


"""
class AttachmentForm(ModelForm)
    class Meta:
        fields = ['attachment', 'text']
        model = Attachment
"""