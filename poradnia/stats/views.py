from django.db.models import F, Func, IntegerField, Case, Sum, When
from braces.views import JSONResponseMixin, SuperuserRequiredMixin
from django.views.generic import TemplateView
from django.views.generic import View
from cases.models import Case as CaseModel


class ApiListViewMixin(JSONResponseMixin):
    def get(self, request, *args, **kwargs):
        return self.render_json_response(list(self.get_object_list()))


class StatsIndexView(TemplateView):
    template_name = 'stats/index.html'


class StatsCaseView(SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/cases.html'


class StatsCaseRenderView(SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/render/cases.html'


class StatsCaseApiView(SuperuserRequiredMixin, ApiListViewMixin, View):
    def get_object_list(self):
        return (
            CaseModel.objects.annotate(
                                        month=Func(F('created_on'),
                                                   function='month',
                                                   output_field=IntegerField())
            ).annotate(
                        year=Func(F('created_on'),
                                  function='year',
                                  output_field=IntegerField())
            ).values('month', 'year')
            .annotate(
                open=Sum(
                    Case(
                        When(status=CaseModel.STATUS.free, then=1),
                        default=0,
                        output_field=IntegerField()
                    )
                ),
                assigned=Sum(
                    Case(
                        When(status=CaseModel.STATUS.assigned, then=1),
                        default=0,
                        output_field=IntegerField()
                    )
                ),
                closed=Sum(
                    Case(
                        When(status=CaseModel.STATUS.closed, then=1),
                        default=0,
                        output_field=IntegerField()
                    )
                )
            ).values('month', 'year', 'open', 'assigned', 'closed')
            .order_by(F('year'), F('month'))
        )
