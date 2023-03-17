from django.contrib import admin

from .models import Record


class RecordInline(admin.StackedInline):
    """
    Stacked Inline View for Record
    """

    model = Record


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    # inlines = [RecordInline]
    date_hierarchy = "created_on"
    list_display = [
        "id",
        "created_on",
        "case",
        "letter",
        "event",
        "courtcase",
        "content_type",
    ]
    # list_filter = []
    search_fields = ["case__name"]
    ordering = ("-created_on",)
    actions = None
