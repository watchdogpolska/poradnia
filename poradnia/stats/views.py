import json

from django.db.models import F, Func, Count, IntegerField
from django.http import JsonResponse

from cases.models import Case

def case_stats_view(request):
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

    return JsonResponse(json.dumps(list(qs)), safe=False)
