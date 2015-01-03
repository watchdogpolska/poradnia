from django.contrib import admin
from .models import Case
from .permissions.models import Permission


class PermissionInline(admin.TabularInline):
    model = Permission


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'client']
    inlines = [PermissionInline, ]
