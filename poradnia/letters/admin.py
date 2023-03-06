from django.contrib import admin
from django.utils.translation import gettext_lazy as _

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

    date_hierarchy = "created_on"
    list_display = (
        "pk",
        "genre",
        "status",
        "name",
        "get_case",
        "created_by",
        "created_by_is_staff",
        "created_on",
        "modified_by",
        "modified_on",
        # "email_from",
        # "email_to",
        "eml",
        # "message_id_header",
    )
    list_filter = (
        "genre",
        "status",
    )
    inlines = [AttachmentInline]
    search_fields = (
        "title",
        # "text",
        "record__case__name",
        "eml",
        # "message_id_header",
        # "email_from",
        # "email_to",
    )
    raw_id_fields = ()
    list_editable = ()
    ordering = ("-pk",)
    actions = None

    @admin.display(
        description=_("Case name"),
        ordering="record__case",
    )
    def get_case(self, obj):
        return obj.record.case
