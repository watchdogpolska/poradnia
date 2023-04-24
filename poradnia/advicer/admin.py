from django.contrib import admin
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .models import Advice, Area, InstitutionKind, Issue, PersonKind


class NullCaseFilter(admin.SimpleListFilter):
    title = _('Case field is null')
    parameter_name = 'one_to_one_null'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Yes')),
            ('no', _('No')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(case__isnull=True)
        elif self.value() == 'no':
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


@admin.register(Issue, InstitutionKind, PersonKind, Area)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    ordering = ("name",)
    actions = None
