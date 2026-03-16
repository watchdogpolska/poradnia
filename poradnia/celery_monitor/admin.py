from django.contrib import admin
from django.utils.html import format_html
from django_celery_results.models import TaskResult

from .models import (
    MonitoringAlert,
    QueueSnapshot,
    SystemHealthCheck,
    TaskSlaSnapshot,
    WorkerHeartbeat,
)


def _status_badge(status):
    color_map = {
        "ok": "#2e7d32",
        "warn": "#ed6c02",
        "crit": "#d32f2f",
        "fail": "#d32f2f",
        "stale": "#d32f2f",
        "missing": "#6a1b9a",
    }
    color = color_map.get(status, "#455a64")
    return format_html(
        '<span style="padding:3px 8px;border-radius:10px;color:white;'
        'background:{};font-weight:600;">{}</span>',
        color,
        status.upper(),
    )


@admin.register(SystemHealthCheck)
class SystemHealthCheckAdmin(admin.ModelAdmin):
    list_display = (
        "singleton_key",
        "status_badge",
        "db_ok",
        "db_latency_ms",
        "broker_ok",
        "broker_latency_ms",
        "checked_at",
        "worker_hostname",
    )
    readonly_fields = [f.name for f in SystemHealthCheck._meta.fields]

    @admin.display(description="Status")
    def status_badge(self, obj):
        return _status_badge(obj.status)

    # Disable add
    def has_add_permission(self, request):
        return False

    # Disable edit
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(QueueSnapshot)
class QueueSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "queue_name",
        "vhost",
        "status_badge",
        "messages_ready",
        "messages_unacknowledged",
        "messages",
        "consumers",
        "checked_at",
    )
    list_filter = ("status", "vhost")
    search_fields = ("queue_name",)
    readonly_fields = [f.name for f in QueueSnapshot._meta.fields]

    @admin.display(description="Status")
    def status_badge(self, obj):
        return _status_badge(obj.status)

    # Disable add
    def has_add_permission(self, request):
        return False

    # Disable edit
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(WorkerHeartbeat)
class WorkerHeartbeatAdmin(admin.ModelAdmin):
    list_display = (
        "worker_name",
        "status_badge",
        "last_seen_at",
        "ping_ok",
        "hostname",
        "pid",
    )
    list_filter = ("status", "ping_ok")
    search_fields = ("worker_name", "hostname")
    readonly_fields = [f.name for f in WorkerHeartbeat._meta.fields]

    @admin.display(description="Status")
    def status_badge(self, obj):
        return _status_badge(obj.status)

    # Disable add
    def has_add_permission(self, request):
        return False

    # Disable edit
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(MonitoringAlert)
class MonitoringAlertAdmin(admin.ModelAdmin):
    list_display = (
        "severity",
        "title",
        "source",
        "is_resolved",
        "email_send_count",
        "email_last_sent_at",
        "first_seen_at",
        "last_seen_at",
        "resolved_at",
    )
    list_filter = ("severity", "is_resolved", "source")
    search_fields = ("title", "message", "dedupe_key")
    readonly_fields = [f.name for f in MonitoringAlert._meta.fields]

    # Disable add
    def has_add_permission(self, request):
        return False

    # Disable edit
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(TaskSlaSnapshot)
class TaskSlaSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "probe_name",
        "queue_name",
        "status_badge",
        "lag_ms",
        "enqueued_at",
        "started_at",
        "worker_hostname",
    )
    list_filter = ("status", "queue_name")
    readonly_fields = [f.name for f in TaskSlaSnapshot._meta.fields]

    @admin.display(description="Status")
    def status_badge(self, obj):
        return _status_badge(obj.status)

    # Disable add
    def has_add_permission(self, request):
        return False

    # Disable edit
    def has_change_permission(self, request, obj=None):
        return False


class TaskResultAdmin(admin.ModelAdmin):
    """Readonly admin for Celery results."""

    list_display = (
        "task_id",
        "periodic_task_name",
        "task_name",
        "status",
        "date_done",
        "worker",
    )
    readonly_fields = [f.name for f in TaskResult._meta.fields]
    ordering = ("-date_done",)
    list_filter = (
        "periodic_task_name",
        "task_name",
        "status",
        "date_done",
        "worker",
    )
    search_fields = (
        "task_id",
        "task_name",
    )
    date_hierarchy = "date_done"

    # Disable add
    def has_add_permission(self, request):
        return False

    # Disable edit
    def has_change_permission(self, request, obj=None):
        return False

    # Disable delete
    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            return False
        return True


admin.site.unregister(TaskResult)
admin.site.register(TaskResult, TaskResultAdmin)
