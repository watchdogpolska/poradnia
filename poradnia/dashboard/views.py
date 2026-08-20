from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView, View

from poradnia.utils.view_mixins import StaffuserRequiredMixin

from . import excel, reports


class StaffDashboardMixin(StaffuserRequiredMixin):
    raise_exception = True


class YearMixin:
    def get_current_year(self):
        return timezone.now().year

    def get_years(self):
        return range(self.get_current_year(), reports.MIN_YEAR - 1, -1)

    def get_selected_year(self):
        current_year = self.get_current_year()
        try:
            year = int(self.request.GET.get("year", current_year))
        except ValueError:
            year = current_year
        if year < reports.MIN_YEAR or year > current_year:
            year = current_year
        return year


class DashboardView(StaffDashboardMixin, YearMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "years": self.get_years(),
                "current_year": self.get_current_year(),
                "summary_report": reports.summary_report(),
            }
        )
        return context


class CasesTabView(StaffDashboardMixin, YearMixin, TemplateView):
    template_name = "dashboard/_cases_tables.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.get_selected_year()
        context["cases_reports"] = [
            reports.users_report(year),
            reports.cases_report(year),
            reports.staff_letters_report(year),
        ]
        return context


class AdvicesTabView(StaffDashboardMixin, YearMixin, TemplateView):
    template_name = "dashboard/_advices_tables.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.get_selected_year()
        context["advices_reports"] = [
            reports.issues_report(year),
            reports.areas_report(year),
            reports.institution_kind_report(year),
            reports.person_kind_report(year),
        ]
        return context


class JudgementsTabView(StaffDashboardMixin, TemplateView):
    template_name = "dashboard/_judgements_tables.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["judgements_reports"] = [
            reports.courtsessions_report(),
            reports.courtcase_report(),
        ]
        return context


class ExcelExportView(StaffDashboardMixin, YearMixin, View):
    def get(self, request, *args, **kwargs):
        year = self.get_selected_year()
        workbook = excel.build_workbook(year)

        response = HttpResponse(
            content_type=(
                "application/vnd.openxmlformats-officedocument" ".spreadsheetml.sheet"
            )
        )
        response["Content-Disposition"] = (
            f'attachment; filename="dashboard_{year}.xlsx"'
        )
        workbook.save(response)
        return response
