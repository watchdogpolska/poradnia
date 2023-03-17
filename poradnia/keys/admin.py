from django.contrib import admin

from .models import Key


@admin.register(Key)
class KeyAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "description", "created_on", "used_on", "download_on"]
    search_fields = ["user", "description"]
    actions = None
