from django.contrib import admin
from django.utils.translation import ugettext as _
from guardian.admin import GuardedModelAdmin

from poradnia.records.admin import RecordInline
from .models import Case, PermissionGroup


@admin.register(Case)
class CaseAdmin(GuardedModelAdmin):
    inlines = [RecordInline]
    list_display = ['name', 'client', 'record_count']

    def record_count(self, obj):
        return obj.record_count

    def get_queryset(self, *args, **kwargs):
        qs = super(CaseAdmin, self).get_queryset(*args, **kwargs)
        return qs.with_record_count()


@admin.register(PermissionGroup)
class PermissionGroupAdmin(admin.ModelAdmin):
    '''
        Admin View for PermissionGroup
    '''
    list_display = ['name', 'get_permissions']
    select_related = ['permissions']

    def get_permissions(self, obj):
        return ", ".join([_(x.name) for x in obj.permissions.all()])

    def get_queryset(self, request):
        qs = super(PermissionGroupAdmin, self).get_queryset(request)
        return qs.prefetch_related('permissions')
