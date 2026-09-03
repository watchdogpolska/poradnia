from django.contrib import admin
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .models import Advice, Area, InstitutionKind, Issue, PersonKind, Scope


class NullCaseFilter(admin.SimpleListFilter):
    title = _("Case field is null")
    parameter_name = "one_to_one_null"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(case__isnull=True)
        elif self.value() == "no":
            return queryset.filter(~Q(case__isnull=True))
        else:
            return queryset


@admin.register(Advice)
class AdviceAdmin(admin.ModelAdmin):
    readonly_fields = ("created_on", "created_by", "modified_by", "modified_on")
    date_hierarchy = "created_on"
    list_display = [
        "id",
        "created_on",
        "advicer",
        "__str__",
        "grant_on",
        "person_kind",
        "institution_kind",
        "case",
        "visible",
    ]
    # list_display_links = ["__str__"]
    list_filter = [
        NullCaseFilter,
        "advicer",
        "visible",
        "person_kind",
        "institution_kind",
    ]
    search_fields = ["id", "user", "description"]
    actions = None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.for_user(request.user)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Scope)
class ScopeAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    ordering = ("name",)
    actions = None
    list_display = [
        "id",
        "name",
        "is_dip",
        "is_local_government",
        "is_slapp",
        "is_out_of_scope",
        "active",
    ]
    list_filter = [
        "is_dip",
        "is_local_government",
        "is_slapp",
        "is_out_of_scope",
        "active",
    ]


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    ordering = ("name",)
    actions = None
    list_display = [
        "id",
        "name",
        "is_dip",
        "is_local_government",
        "is_slapp",
        "active",
    ]
    list_filter = [
        "is_dip",
        "is_local_government",
        "is_slapp",
        "active",
    ]


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    ordering = ("name",)
    actions = None
    list_display = [
        "id",
        "name",
        "is_dip",
        "is_local_government",
        "is_slapp",
        "active",
    ]
    list_filter = [
        "is_dip",
        "is_local_government",
        "is_slapp",
        "active",
    ]


@admin.register(InstitutionKind)
class InstitutionKindAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    ordering = ("name",)
    actions = None
    list_display = [
        "id",
        "name",
        "is_undefined",
        "active",
    ]
    list_filter = [
        "is_undefined",
        "active",
    ]


@admin.register(PersonKind)
class PersonKindAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    ordering = ("name",)
    actions = None
    list_display = [
        "id",
        "name",
        "is_undefined",
        "active",
    ]
    list_filter = [
        "is_undefined",
        "active",
    ]
