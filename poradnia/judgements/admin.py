from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

# Register your models here.
from poradnia.judgements.models import Court, CourtCase, CourtSession
from poradnia.judgements.registry import get_parser_keys


class CourtAdminForm(forms.ModelForm):
    class Meta:
        model = Court
        widgets = {
            "parser_key": forms.RadioSelect(
                choices=[(x, x) for x in get_parser_keys()] + [("", _("None"))]
            )
        }
        fields = "__all__"


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "active", "parser_key", "get_parser_status"]
    list_filter = ["active", "parser_key"]
    form = CourtAdminForm
    search_fields = ["name", "parser_key"]
    actions = None

    @admin.display(
        description="Parser status",
        boolean=True,
        ordering="parser_status",
    )
    def get_parser_status(self, obj):
        return obj.parser_status


@admin.register(CourtCase)
class CourtCaseAdmin(admin.ModelAdmin):
    list_display = ["id", "court", "signature", "created_by", "modified_by"]
    search_fields = ["court", "signature", "created_by", "modified_by"]
    list_filter = ["court"]
    actions = None


@admin.register(CourtSession)
class CourtSessionAdmin(admin.ModelAdmin):
    list_display = ["id", "get_courtcase_signature", "get_event_subject", "parser_key"]
    list_filter = ["parser_key"]
    search_fields = ["courtcase", "event", "parser_key"]
    actions = None

    def get_courtcase_signature(self, obj):
        return obj.courtcase.signature

    def get_event_subject(self, obj):
        return obj.event.text
