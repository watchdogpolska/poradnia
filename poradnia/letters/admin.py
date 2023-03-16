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
        "get_case_name",
        "created_by",
        "created_by_is_staff",
        "created_on",
        "modified_by",
        "modified_on",
        "eml",
    )
    list_filter = (
        "genre",
        "status",
    )
    inlines = [AttachmentInline]
    search_fields = (
        "name",
        "record__case__name",
        "eml",
    )
    raw_id_fields = ()
    list_editable = ()
    ordering = ("-pk",)
    actions = None

    @admin.display(
        description=_("Case name"),
        ordering="record__case",
    )

    def get_case_name(self, obj):
        return obj.record.case.name

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.select_related('record__case')
