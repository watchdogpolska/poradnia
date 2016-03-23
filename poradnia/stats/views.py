from django.db.models import F, Func, IntegerField, Case, Sum, When, Min
from braces.views import JSONResponseMixin, SuperuserRequiredMixin
from django.views.generic import TemplateView
from django.views.generic import View
from cases.models import Case as CaseModel
from letters.models import Letter as LetterModel

SECONDS_IN_A_DAY = 60 * 60 * 24

class ApiListViewMixin(JSONResponseMixin):
    def get(self, request, *args, **kwargs):
        return self.render_json_response(list(self.get_object_list()))


class StatsIndexView(TemplateView):
    template_name = 'stats/index.html'


class StatsCaseCreatedView(SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/cases/cases_created.html'


class StatsCaseCreatedRenderView(SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/render/cases/cases_created.html'


class StatsCaseCreatedApiView(SuperuserRequiredMixin, ApiListViewMixin, View):
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


class StatsCaseReactionRenderView(SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/render/cases/reaction.html'


class StatsCaseReactionApiView(SuperuserRequiredMixin, ApiListViewMixin, View):
    def get_object_list(self):
        qs = (
            CaseModel.objects.filter(
                letter__status=LetterModel.STATUS.done
            ).filter(
                letter__created_by__is_staff=True
            ).annotate(
                first_accepted=Min('letter__accept')
            # ).annotate(
            #     delta=ExpressionWrapper(
            #         F('letter__accept') - F('created_on'),
            #         output_field=IntegerField()
            #     )  # Django bug?
            ).values(
                'first_accepted', 'created_on'
            )
        )

        deltas = {}
        for el in qs:
            date = str(el['created_on'].year) + '.' + str(el['created_on'].month).zfill(2)
            time_delta = (el['first_accepted'] - el['created_on']).total_seconds()
            if date in deltas:
                deltas[date].append(time_delta)
            else:
                deltas[date] = [time_delta]


        return [{
            'date': date,
            'time_delta': int(sum(deltas[date]) / len(deltas[date]) / SECONDS_IN_A_DAY)
        } for date in sorted(deltas.keys())]
