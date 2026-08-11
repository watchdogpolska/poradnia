from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from .models import N8nArticlesSearchRequest, N8nCaseTagsRequest

HEADER_FONT = Font(bold=True)
HEADER_FILL = PatternFill(
    start_color="FFDDDDDD", end_color="FFDDDDDD", fill_type="solid"
)


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
        for col_idx in range(1, len(columns) + 1):
            cell = sheet.cell(row=1, column=col_idx)
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL

        case_url_col = columns.index("case_absolute_url") + 1
        letter_url_col = columns.index("letter_absolute_url") + 1

        queryset = queryset.select_related(
            "case", "letter", "accepted_by", "rejected_by"
        )
        for obj in queryset:
            case_url = (
                request.build_absolute_uri(obj.case.get_absolute_url())
                if obj.case_id
                else ""
            )
            letter_url = (
                request.build_absolute_uri(obj.letter.get_absolute_url())
                if obj.letter_id
                else ""
            )
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
                    case_url,
                    obj.letter_id,
                    letter_url,
                    str(obj.accepted_by) if obj.accepted_by_id else "",
                    str(obj.rejected_by) if obj.rejected_by_id else "",
                    _naive(obj.updated_at),
                    obj.response,
                ]
            )
            row_idx = sheet.max_row
            sheet.cell(row=row_idx, column=len(columns)).alignment = Alignment(
                wrap_text=True, vertical="top"
            )
            for url, col_idx in (
                (case_url, case_url_col),
                (letter_url, letter_url_col),
            ):
                if url:
                    cell = sheet.cell(row=row_idx, column=col_idx)
                    cell.hyperlink = url
                    cell.style = "Hyperlink"

        sheet.auto_filter.ref = sheet.dimensions

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
