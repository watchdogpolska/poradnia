from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType

class LogEntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'action_time'
    list_display = ('action_time', 'user', 'action_flag', 'content_type', 'object_id', 'object_repr')
    list_filter = ('action_flag', 'content_type')
    search_fields = ('object_repr', 'change_message', 'user__username', 'user__first_name', 'user__last_name')
    actions = None

    def content_type(self, obj):
        return obj.content_type.name

    content_type.short_description = 'Type'

    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(LogEntry, LogEntryAdmin)
