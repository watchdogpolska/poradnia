from django.contrib import admin
from .models import Permission, LocalGroup


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['case', 'group', 'user']


@admin.register(LocalGroup)
class SiteGroupAdmin(admin.ModelAdmin):
    list_display = ['pk', 'rank', 'group']
