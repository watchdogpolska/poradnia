from django.contrib import admin
from .models import Case, Permission, SiteGroup


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'client']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['case', 'rank', 'user']


@admin.register(SiteGroup)
class SiteGroupAdmin(admin.ModelAdmin):
    list_display = ['pk', 'rank', 'site', 'group']
