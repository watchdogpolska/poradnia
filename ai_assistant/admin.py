from django.contrib import admin

from .models import N8nArticlesSearchRequest


@admin.register(N8nArticlesSearchRequest)
class N8nArticlesSearchRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "request_id",
        "environment",
        "status",
        "is_foi",
        "direct_search",
        "case",
        "created_at",
        "updated_at",
    )
    list_filter = ("environment", "status", "is_foi", "direct_search")
    search_fields = ("request_id", "question", "response")
    date_hierarchy = "created_at"
    raw_id_fields = ("case",)

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
