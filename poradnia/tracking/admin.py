from django.contrib import admin
from .models import Following


class FollowingAdmin(admin.ModelAdmin):
    list_display = ['user', 'case']
admin.site.register(Following, FollowingAdmin)
