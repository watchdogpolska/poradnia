from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from openpyxl import Workbook
from openpyxl.styles import Alignment

from .models import N8nArticlesSearchRequest, N8nCaseTagsRequest


def _naive(dt):
    return timezone.localtime(dt).replace(tzinfo=None) if dt else ""


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
        "letter",
        "accepted_by",
        "rejected_by",
        "created_at",
        "updated_at",
    )
    list_filter = ("environment", "status", "is_foi", "direct_search")
    search_fields = ("request_id", "question", "response")
    date_hierarchy = "created_at"
    raw_id_fields = ("case", "letter")
    actions = ["export_as_excel"]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.action(description=_("Export selected as Excel report"))
    def export_as_excel(self, request, queryset):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "N8nArticlesSearchRequest"

        columns = [
            "id",
            "created_at",
            "request_id",
            "environment",
            "status",
            "is_foi",
            "direct_search",
            "case_id",
            "case_absolute_url",
            "letter_id",
            "letter_absolute_url",
            "accepted_by",
            "rejected_by",
            "updated_at",
            "response",
        ]
        sheet.append(columns)

        queryset = queryset.select_related(
            "case", "letter", "accepted_by", "rejected_by"
        )
        for obj in queryset:
            sheet.append(
                [
                    obj.id,
                    _naive(obj.created_at),
                    obj.request_id,
                    obj.environment,
                    obj.status,
                    obj.is_foi,
                    obj.direct_search,
                    obj.case_id,
                    (
                        request.build_absolute_uri(obj.case.get_absolute_url())
                        if obj.case_id
                        else ""
                    ),
                    obj.letter_id,
                    (
                        request.build_absolute_uri(obj.letter.get_absolute_url())
                        if obj.letter_id
                        else ""
                    ),
                    str(obj.accepted_by) if obj.accepted_by_id else "",
                    str(obj.rejected_by) if obj.rejected_by_id else "",
                    _naive(obj.updated_at),
                    obj.response,
                ]
            )
            sheet.cell(row=sheet.max_row, column=len(columns)).alignment = Alignment(
                wrap_text=True, vertical="top"
            )

        response = HttpResponse(
            content_type=(
                "application/vnd.openxmlformats-officedocument" ".spreadsheetml.sheet"
            )
        )
        response["Content-Disposition"] = (
            'attachment; filename="n8n_articles_search_requests.xlsx"'
        )
        workbook.save(response)
        return response


@admin.register(N8nCaseTagsRequest)
class N8nCaseTagsRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "request_id",
        "environment",
        "status",
        "case",
        "accepted_by",
        "rejected_by",
        "created_at",
        "updated_at",
    )
    list_filter = ("environment", "status")
    search_fields = ("request_id", "question", "response")
    date_hierarchy = "created_at"
    raw_id_fields = ("case",)

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
