from django.contrib import admin
from import_export.admin import ImportExportMixin

from .models import Advice, Area, InstitutionKind, Issue, PersonKind


@admin.register(Advice)
class AdviceAdmin(admin.ModelAdmin):
    readonly_fields = ("created_on", "created_by", "modified_by", "modified_on")
    list_display = [
        "created_on",
        "advicer",
        "__str__",
        "person_kind",
        "institution_kind",
        "visible",
    ]
    list_display_links = ["__str__"]
    list_filter = ["created_on", "grant_on", "advicer", "visible"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.for_user(request.user)


@admin.register(Issue, InstitutionKind, PersonKind, Area)
class CategoryAdmin(ImportExportMixin, admin.ModelAdmin):
    pass
