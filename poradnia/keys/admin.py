from django.contrib import admin
from django.http.request import HttpRequest

from .models import Key


@admin.register(Key)
class KeyAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "description", "created_on", "used_on", "download_on"]
    search_fields = ["user", "description"]
    readonly_fields = [
        "user",
        "password",
        "created_on",
        "used_on",
        "description",
        "download_on",
    ]
    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_password(self, obj):
        if self.request.user == obj.user:
            return obj.password
        return "****hidden for security reasons****"

    def get_object(self, request: HttpRequest, object_id: str, from_field: None = ...):
        obj = super().get_object(request, object_id, from_field)
        if request.user == obj.user:
            return obj
        obj.password = "****hidden for security reasons****"
        return obj
