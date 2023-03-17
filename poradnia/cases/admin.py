from django.contrib import admin
from django.utils.translation import gettext as _
from guardian.admin import GuardedModelAdmin

from poradnia.records.admin import RecordInline

from .models import Case, PermissionGroup


@admin.register(Case)
class CaseAdmin(GuardedModelAdmin):
    inlines = [RecordInline]
    date_hierarchy = "created_on"
    list_display = [
        "id",
        "name",
        "created_on",
        "deadline",
        "status",
        "client",
        "record_count",
        "handled",
        "has_project",
    ]
    list_filter = [
        "status",
        "has_project",
        "handled",
    ]
    search_fields = ["name", "client"]
    actions = None

    def record_count(self, obj):
        return obj.record_count

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.with_record_count()


@admin.register(PermissionGroup)
class PermissionGroupAdmin(admin.ModelAdmin):
    """
    Admin View for PermissionGroup
    """

    list_display = ["name", "get_permissions"]
    select_related = ["permissions"]
    actions = None

    def get_permissions(self, obj):
        return ", ".join([_(x.name) for x in obj.permissions.all()])

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("permissions")
