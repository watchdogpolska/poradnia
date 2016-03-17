import json

from django.db.models import F, Func, Count, IntegerField, Case, Sum, When
from django.http import JsonResponse
from django.views.generic import TemplateView

from cases.models import Case as CaseModel


def case_stats_api_view(request):
    qs = (
        CaseModel.objects.annotate(
            month=Func(F('created_on'),
            function='month',
            output_field=IntegerField())
        ).annotate(
            year=Func(F('created_on'),
            function='year',
            output_field=IntegerField())
        ).values('month','year')
        .annotate(
            count_open=Sum(
                Case(
                    When(status=CaseModel.STATUS.free, then=1),
                    default=0,
                    output_field=IntegerField()
                )
            ),
            count_assigned=Sum(
                Case(
                    When(status=CaseModel.STATUS.assigned, then=1),
                    default=0,
                    output_field=IntegerField()
                )
            ),
            count_closed=Sum(
                Case(
                    When(status=CaseModel.STATUS.closed, then=1),
                    default=0,
                    output_field=IntegerField()
                )
            )
        ).values('month', 'year', 'count_open', 'count_assigned', 'count_closed')
        .order_by(F('year'), F('month'))
    )

    return JsonResponse(list(qs), safe=False)


class StatsCaseView(TemplateView):
    template_name = 'stats/cases.html'
    data_view = case_stats_api_view

    def get_context_data(self, **kwargs):
        context = super(StatsCaseView, self).get_context_data(**kwargs)
        return context
