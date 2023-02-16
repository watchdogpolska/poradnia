from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

# Register your models here.
from poradnia.judgements.models import Court
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
    list_display = ["name", "get_parser_status"]
    list_filter = ["parser_key"]
    form = CourtAdminForm

    @admin.display(
        description="Parser status",
        boolean=True,
        ordering="parser_status",
    )
    def get_parser_status(self, obj):
        return obj.parser_status
