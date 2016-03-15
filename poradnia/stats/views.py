import json

from django.db.models import F, Func, Count, IntegerField
from django.http import JsonResponse
from django.views.generic import TemplateView

from cases.models import Case


def case_stats_api_view(request):
    qs = (
        Case.objects.annotate(
            month=Func(F('created_on'),
            function='month',
            output_field=IntegerField())
        ).annotate(
            year=Func(F('created_on'),
            function='year',
            output_field=IntegerField())
        ).values('month','year')
        .annotate(
            count=Count(F('id'))
        ).values('month','year','count')
        .order_by(F('year'), F('month'))
    )

    return JsonResponse(list(qs), safe=False)


class StatsCaseView(TemplateView):
    template_name = 'stats/cases.html'
    data_view = case_stats_api_view

    def get_context_data(self, **kwargs):
        context = super(StatsCaseView, self).get_context_data(**kwargs)
        return context
