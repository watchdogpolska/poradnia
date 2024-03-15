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

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_delete"] = False
        return super().change_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context,
        )
