from django.contrib import admin

from .models import Event, Reminder


class ReminderInline(admin.StackedInline):
    model = Reminder
    readonly_fields = ["user"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    date_hierarchy = "time"
    inlines = [ReminderInline]
    list_display = [
        "id",
        "case__id",
        "deadline",
        "completed",
        "public",
        "time",
    ]
    list_filter = ["completed"]
    search_fields = ["id", "name", "location"]
    ordering = ["-id"]
    actions = None
    readonly_fields = [
        "id",
        "case",
        "created_by",
        "created_on",
        "modified_by",
        "modified_on",
    ]
