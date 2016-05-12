from datetime import datetime
from dateutil.rrule import MONTHLY

from django.db.models import F, Func, IntegerField, Case, Sum, When, Min, Count
from django.shortcuts import redirect
from braces.views import JSONResponseMixin, LoginRequiredMixin, SuperuserRequiredMixin
from django.views.generic import TemplateView
from django.views.generic import View

from cases.models import Case as CaseModel
from letters.models import Letter as LetterModel
from .utils import raise_unless_unauthenticated, GapFiller, SECONDS_IN_A_DAY, DATE_FORMAT


class ApiListViewMixin(JSONResponseMixin):
    def get(self, request, *args, **kwargs):
        return self.render_json_response(self.get_object_list())


class StatsIndexView(TemplateView):
    template_name = 'stats/index.html'


class StatsCaseCreatedView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/cases/created.html'
    raise_exception = raise_unless_unauthenticated


class StatsCaseCreatedRenderView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/render/cases/created.html'
    raise_exception = raise_unless_unauthenticated


class StatsCaseCreatedApiView(LoginRequiredMixin, SuperuserRequiredMixin, ApiListViewMixin, View):
    raise_exception = raise_unless_unauthenticated

    def get_object_list(self):
        qs = list(
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

        qs = [{
            'date': datetime(obj['year'], obj['month'], 1),
            'open': obj['open'],
            'assigned': obj['assigned'],
            'closed': obj['closed']
        } for obj in qs]

        return GapFiller(
            qs,
            MONTHLY,
            'date',
            DATE_FORMAT
        ).fill_gaps()


class StatsCaseReactionView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/cases/reaction.html'
    raise_exception = raise_unless_unauthenticated


class StatsCaseReactionRenderView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/render/cases/reaction.html'
    raise_exception = raise_unless_unauthenticated


class StatsCaseReactionApiView(LoginRequiredMixin, SuperuserRequiredMixin, ApiListViewMixin, View):
    raise_exception = raise_unless_unauthenticated

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
        for obj in qs:
            date = datetime(obj['created_on'].year, obj['created_on'].month, 1)
            time_delta = (obj['first_accepted'] - obj['created_on']).total_seconds()
            if date in deltas:
                deltas[date].append(time_delta)
            else:
                deltas[date] = [time_delta]

        qs = [{
            'date': date,
            'reaction_time': int(sum(deltas[date]) / len(deltas[date]) / SECONDS_IN_A_DAY)
        } for date in sorted(deltas.keys())]

        return GapFiller(
            qs,
            MONTHLY,
            'date',
            DATE_FORMAT
        ).fill_gaps()


class StatsCaseUnansweredView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/cases/unanswered.html'
    raise_exception = raise_unless_unauthenticated


class StatsCaseUnansweredRenderView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/render/cases/unanswered.html'
    raise_exception = raise_unless_unauthenticated


class StatsCaseUnansweredApiView(LoginRequiredMixin, SuperuserRequiredMixin, ApiListViewMixin, View):
    raise_exception = raise_unless_unauthenticated

    def get_object_list(self):
        qs =  (
            CaseModel.objects.filter(
                                        last_send=None
            ).annotate(
                        month=Func(F('created_on'),
                                   function='month',
                                   output_field=IntegerField())
            ).annotate(
                        year=Func(F('created_on'),
                                  function='year',
                                  output_field=IntegerField())
            ).values('month', 'year')
        ).annotate(
            count=Count('pk')
        ).values(
            'month', 'year', 'count'
        ).order_by(F('year'), F('month'))

        qs = [{
            'date': datetime(obj['year'], obj['month'], 1),
            'count': obj['count']
        } for obj in qs]

        return GapFiller(
            qs,
            MONTHLY,
            'date',
            DATE_FORMAT
        ).fill_gaps()
