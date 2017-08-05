import csv
import json
from collections import OrderedDict
from datetime import datetime
from itertools import takewhile, dropwhile

from braces.views import (JSONResponseMixin, LoginRequiredMixin,
                          SuperuserRequiredMixin)
from dateutil.relativedelta import relativedelta
from dateutil.rrule import MONTHLY
from django.db.models import F, Case, Count, IntegerField, Min, Sum, When, Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.datetime_safe import date
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView, View

from poradnia.cases.models import Case as CaseModel
from poradnia.letters.models import Letter as LetterModel
from poradnia.stats.models import Item, Value, Graph
from poradnia.users.models import User as UserModel
from .utils import (DATE_FORMAT_MONTHLY, SECONDS_IN_A_DAY, GapFiller,
                    raise_unless_unauthenticated)


class ApiListViewMixin(JSONResponseMixin):
    def get(self, request, *args, **kwargs):
        return self.render_json_response(self.get_object_list())


class StatsIndexView(TemplateView):
    template_name = 'stats/index.html'

    def get_context_data(self, **kwargs):
        kwargs['item_list'] = Item.objects.for_user(self.request.user).all()
        kwargs['graph_list'] = Graph.objects.all()
        return super(StatsIndexView, self).get_context_data(**kwargs)


class StatsCaseCreatedView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/cases/created.html'
    raise_exception = raise_unless_unauthenticated


class StatsCaseCreatedRenderView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/render/cases/created.html'
    raise_exception = raise_unless_unauthenticated


class StatsCaseCreatedApiView(LoginRequiredMixin, SuperuserRequiredMixin, ApiListViewMixin, View):
    raise_exception = raise_unless_unauthenticated

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
            date = "{0:04d}-{1:02d}".format(obj['created_on'].year, obj['created_on'].month)
            time_delta = (obj['first_accepted'] - obj['created_on']).total_seconds()
            if date in deltas:
                deltas[date].append(time_delta)
            else:
                deltas[date] = [time_delta, ]

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


class StatsCaseUnansweredView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/cases/unanswered.html'
    raise_exception = raise_unless_unauthenticated


class StatsCaseUnansweredRenderView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/render/cases/unanswered.html'
    raise_exception = raise_unless_unauthenticated


class StatsCaseUnansweredApiView(LoginRequiredMixin, SuperuserRequiredMixin, ApiListViewMixin,
                                 View):
    raise_exception = raise_unless_unauthenticated

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


class StatsLetterCreatedView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/letters/created.html'
    raise_exception = raise_unless_unauthenticated


class StatsLetterCreatedRenderView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/render/letters/created.html'
    raise_exception = raise_unless_unauthenticated


class StatsLetterCreatedApiView(LoginRequiredMixin, SuperuserRequiredMixin, ApiListViewMixin, View):
    raise_exception = raise_unless_unauthenticated

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


class StatsUserRegisteredView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/users/registered.html'
    raise_exception = raise_unless_unauthenticated


class StatsUserRegisteredRenderView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'stats/render/users/registered.html'
    raise_exception = raise_unless_unauthenticated


class StatsUserRegisteredApiView(LoginRequiredMixin, SuperuserRequiredMixin, ApiListViewMixin, View):
    raise_exception = raise_unless_unauthenticated

    def get_object_list(self):
        qs = UserModel.objects.with_month_year().values(
            'month', 'year'
        ).annotate(
            count=Count('pk')
        ).order_by(
            F('year'), F('month')
        )

        INIT_DATE = (2016, 11)  # all users created before have null `created_on` values

        # NOTE: hardcoded for now, some day url parameters will be allowed
        start_date = INIT_DATE

        def not_after_start_date(x):
            return (x['year'] is None or x['month'] is None) or \
                   (x['year'] < start_date[0]) or \
                   (x['year'] == start_date[0] and x['month'] <= start_date[1])

        before = list(takewhile(not_after_start_date, qs))
        after = list(dropwhile(not_after_start_date, qs))

        total_before = sum([x['count'] for x in before])
        start_date_obj = {
            'year': start_date[0],
            'month': start_date[1],
            'count': total_before
        }

        selected_dates = [start_date_obj] + after

        serialized = [{
            'date': "{0:04d}-{1:02d}".format(obj['year'], obj['month']),
            'count': obj['count']
        } for obj in selected_dates]

        filled = GapFiller(
            serialized,
            MONTHLY,
            'date',
            DATE_FORMAT_MONTHLY
        ).fill_gaps()

        total_count = 0
        ans = []
        for obj in filled:
            total_count += obj['count']
            ans.append({
                'date': obj['date'],
                'count': total_count
            })

        return ans


class TimeMixin(object):
    @property
    def today(self):
        today = date.today()
        return today.replace(month=int(self.kwargs.get('month', str(today.month))),
                             year=int(self.kwargs.get('year', str(today.year))))

    @property
    def start(self):
        return self.today.replace(day=1)

    @property
    def end(self):
        return self.today.replace(day=1) + relativedelta(months=1)


class ValueListView(TimeMixin):
    @property
    def item(self):
        return get_object_or_404(Item.objects.for_user(self.request.user),
                                 key=self.kwargs['key'])

    def get_queryset(self):
        return Value.objects.filter(time__lte=self.end, time__gte=self.start).filter(item=self.item).all()


class ValueBrowseListView(ValueListView, TemplateView):
    template_name = "stats/item_details.html"

    def get_context_data(self, **kwargs):
        item = self.item
        kwargs['item'] = item
        kwargs['value_list'] = self.get_queryset()
        kwargs['today'], kwargs['start'], kwargs['end'] = self.today, self.start, self.end
        return super(ValueBrowseListView, self).get_context_data(**kwargs)


class CSVValueListView(ValueListView, View):
    def get(self, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(self.item.key)
        writer = csv.writer(response)
        writer.writerow([_("Key"), _("Name"), _("Time"), _("Time (unix)"), _("Value")])
        for item in self.get_queryset():
            writer.writerow([self.item.key.encode('utf-8'),
                             self.item.name.encode('utf-8'),
                             item.time.strftime("%c"),
                             item.time.strftime("%s"),
                             item.value])
        return response


class JSONValueListView(ValueListView, View):
    def get(self, *args, **kwargs):
        response = HttpResponse(content_type='application/json')
        data = {'item': self.item.as_dict(),
                'values': [o.as_dict() for o in self.get_queryset()]}
        json.dump(data, response, indent=4)
        return response


class GraphTimeMixin(TimeMixin):
    @property
    def object(self):
        if not getattr(self, '_object', None):
            values_qs = Value.objects.filter(time__lte=self.end, time__gte=self.start).all()
            prefetch_obj = Prefetch('items__value_set', values_qs)
            graph_qs = Graph.objects.prefetch_related('items').prefetch_related(prefetch_obj).all()
            self._object = get_object_or_404(graph_qs, pk=self.kwargs['pk'])
        return self._object

    def get_dataset(self, item, times):
        values = {value.time.strftime("%s"): value.value for value in item.value_set.all()}
        data = [values.get(time, None) for time in times]
        label = item.name
        return {'data': data, 'label': label}

    @property
    def times(self):
        if not getattr(self, '_times', None):
            self._times = list({value.time.strftime("%s")
                                for item in self.object.items.all()
                                for value in item.value_set.all()})
            self._times = sorted(self._times)
        return self._times

    def get_graph(self):
        dataset = [self.get_dataset(item, self.times) for item in self.object.items.all()]
        labels = [str(datetime.fromtimestamp(int(time))) for time in self.times]
        return {'datasets': dataset, 'labels': labels}

    def get_table(self):
        header = [item.as_dict() for item in self.object.items.all()]
        data = {}
        for item in self.object.items.all():
            for value in item.value_set.all():
                if item.key not in data:
                    data[item.key] = {}
                data[item.key][value.time.strftime("%s")] = value.value
        body = []
        for time in self.times:
            data_row = OrderedDict((item['key'], data[item['key']].get(time, None)) for item in header)
            body.append({'date': time,
                         'label': str(datetime.fromtimestamp(int(time))),
                         'row': data_row})
        return {'header': header, 'body': body}


class GraphDetailView(GraphTimeMixin, TemplateView):
    template_name = "stats/graph_details.html"

    def get_context_data(self, **kwargs):
        kwargs['object'] = self.object
        kwargs['today'], kwargs['start'], kwargs['end'] = self.today, self.start, self.end
        kwargs['graph'] = self.get_graph()
        kwargs['table'] = self.get_table()
        return super(GraphDetailView, self).get_context_data(**kwargs)

class JSONGraphDetailView(GraphTimeMixin, View):
    def get(self, *args, **kwargs):
        response = HttpResponse(content_type='application/json')
        json.dump(self.get_table(), response, indent=4)
        return response
