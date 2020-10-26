from django.contrib import admin

from .models import Attachment, Letter


class AttachmentInline(admin.StackedInline):
    """
    Stacked Inline View for Attachment
    """

    model = Attachment


@admin.register(Letter)
class LetterAdmin(admin.ModelAdmin):
    """
    Admin View for Letter
    """

    inlines = [AttachmentInline]
