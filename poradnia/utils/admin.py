from django.contrib import admin
from django.contrib.admin.models import LogEntry


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    date_hierarchy = "action_time"
    list_display = (
        "action_time",
        "user",
        "action_flag",
        "content_type",
        "object_id",
        "object_repr",
        "change_message",
    )
    list_filter = ("action_flag", "content_type")
    search_fields = (
        "object_repr",
        "change_message",
        "object_id",
        "user__username",
        "user__first_name",
        "user__last_name",
    )
    actions = None

    @admin.display(description="Type")
    def content_type(self, obj):
        return obj.content_type.name

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False
