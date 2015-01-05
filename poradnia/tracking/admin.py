from django.contrib import admin
from .models import Tracking


@admin.register(Tracking)
class TrackingAdmin(admin.ModelAdmin):
    list_display = ['user', 'case']
