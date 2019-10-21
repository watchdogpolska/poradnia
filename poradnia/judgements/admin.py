from django import forms
from django.contrib import admin

# Register your models here.
from poradnia.judgements.models import Court
from poradnia.judgements.registry import get_parser_keys
from django.utils.translation import ugettext_lazy as _


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
    list_display = ["name", "get_parser_status"]
    list_filter = ["parser_key"]
    form = CourtAdminForm

    def get_parser_status(self, obj):
        return obj.parser_status

    get_parser_status.boolean = True
    get_parser_status.admin_order_field = "parser_status"
    get_parser_status.short_description = "Parser status"
