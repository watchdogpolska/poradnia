from django.contrib import admin

from .models import Advice, Area, InstitutionKind, Issue, PersonKind


@admin.register(Advice)
class AdviceAdmin(admin.ModelAdmin):
    readonly_fields = ("created_on", "created_by", "modified_by", "modified_on")
    date_hierarchy = "created_on"
    list_display = [
        "created_on",
        "advicer",
        "__str__",
        "grant_on",
        "person_kind",
        "institution_kind",
        "visible",
    ]
    list_display_links = ["__str__"]
    list_filter = [
        "advicer",
        "visible",
        "person_kind",
        "institution_kind",
    ]
    search_fields = ["user", "description"]
    actions = None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.for_user(request.user)


@admin.register(Issue, InstitutionKind, PersonKind, Area)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    ordering = ("name",)
    actions = None
