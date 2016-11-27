from braces.views import JSONResponseMixin
from dateutil.rrule import MONTHLY
from django.db.models import F, IntegerField, Case, Sum, When, Min, Count
from django.views.generic import TemplateView
from django.views.generic import View

from cases.models import Case as CaseModel
from letters.models import Letter as LetterModel
from users.utils import SuperuserRequiredMixin
from .utils import GapFiller, SECONDS_IN_A_DAY, DATE_FORMAT_MONTHLY, NoPermissionHandlerMixin


class ApiListViewMixin(JSONResponseMixin):
    def get(self, request, *args, **kwargs):
        return self.render_json_response(self.get_object_list())


class StatsIndexView(TemplateView):
    template_name = 'stats/index.html'


class StatsCaseCreatedView(NoPermissionHandlerMixin, SuperuserRequiredMixin,
                           TemplateView):
    template_name = 'stats/cases/created.html'
    raise_exception = True
    redirect_unauthenticated_users = True


class StatsCaseCreatedRenderView(NoPermissionHandlerMixin,
                                 SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/render/cases/created.html'
    raise_exception = True
    redirect_unauthenticated_users = True


class StatsCaseCreatedApiView(NoPermissionHandlerMixin, SuperuserRequiredMixin,
                              ApiListViewMixin, View):
    raise_exception = True
    redirect_unauthenticated_users = True

    def get_object_list(self):
        qs = CaseModel.objects.with_month_year().values(
            'month', 'year'
            ).annotate(
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
            ).values(
            'month', 'year', 'open', 'assigned', 'closed'
            ).order_by(
            F('year'), F('month')
            )

        result = [{
            'date': "{0:04d}-{1:02d}".format(obj['year'], obj['month']),
            'open': obj['open'],
            'assigned': obj['assigned'],
            'closed': obj['closed']
        } for obj in qs]

        return GapFiller(
            result,
            MONTHLY,
            'date',
            DATE_FORMAT_MONTHLY
        ).fill_gaps()


class StatsCaseReactionView(SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/cases/reaction.html'


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
        for obj in qs:
            date = "{0:04d}-{1:02d}".format(obj['created_on'].year, obj['created_on'].month)
            time_delta = (obj['first_accepted'] - obj['created_on']).total_seconds()
            if date in deltas:
                deltas[date].append(time_delta)
            else:
                deltas[date] = [time_delta]

        result = [{
            'date': date,
            'reaction_time': int(sum(deltas[date]) / len(deltas[date]) / SECONDS_IN_A_DAY)
        } for date in sorted(deltas.keys())]

        return GapFiller(
            result,
            MONTHLY,
            'date',
            DATE_FORMAT_MONTHLY
        ).fill_gaps()


class StatsCaseUnansweredView(SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/cases/unanswered.html'


class StatsCaseUnansweredRenderView(SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/render/cases/unanswered.html'


class StatsCaseUnansweredApiView(SuperuserRequiredMixin, ApiListViewMixin, View):

    def get_object_list(self):
        qs = CaseModel.objects.filter(
            last_send=None
        ).with_month_year().values(
            'month', 'year'
        ).annotate(
            count=Count('pk')
        ).values(
            'month', 'year', 'count'
        ).order_by(F('year'), F('month'))

        qs = [{
            'date': "{0:04d}-{1:02d}".format(obj['year'], obj['month']),
            'count': obj['count']
        } for obj in qs]

        return GapFiller(
            qs,
            MONTHLY,
            'date',
            DATE_FORMAT_MONTHLY
        ).fill_gaps()


class StatsLetterCreatedView(SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/letters/created.html'


class StatsLetterCreatedRenderView(SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/render/letters/created.html'


class StatsLetterCreatedApiView(SuperuserRequiredMixin, ApiListViewMixin, View):

    def get_object_list(self):
        qs = LetterModel.objects.with_month_year().values(
            'month', 'year'
        ).annotate(
                staff=Sum(
                    Case(
                        When(created_by__is_staff=True, then=1),
                        default=0,
                        output_field=IntegerField()
                    )
                ),
                client=Sum(
                    Case(
                        When(created_by__is_staff=False, then=1),
                        default=0,
                        output_field=IntegerField()
                    )
                ),
            ).values(
            'month', 'year', 'client', 'staff'
        ).order_by(F('year'), F('month'))

        qs = [{
            'date': "{0:04d}-{1:02d}".format(obj['year'], obj['month']),
            'staff': obj['staff'],
            'client': obj['client']
        } for obj in qs]

        return GapFiller(
            qs,
            MONTHLY,
            'date',
            DATE_FORMAT_MONTHLY
        ).fill_gaps()
