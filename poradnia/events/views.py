from django.utils.html import mark_safe
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.views.generic import MonthArchiveView, ArchiveIndexView
from django.views.generic.list import BaseListView
from django.utils.timezone import now
from django.conf import settings
from dateutil.relativedelta import relativedelta
from braces.views import SelectRelatedMixin, LoginRequiredMixin
from cases.models import Case
from users.utils import PermissionMixin
from keys.mixins import KeyAuthMixin
from .models import Event
from .forms import EventForm
from .utils import EventCalendar


@login_required
def add(request, case_pk):
    context = {}

    case = get_object_or_404(Case, pk=case_pk)

    case.perm_check(request.user, 'can_add_record')
    context['case'] = case

    form = EventForm.partial(case=case, user=request.user)

    if request.method == 'POST':
        form = form(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request,
                _("Success added new event %(event)s") % {'event': obj, })
            return HttpResponseRedirect(case.get_absolute_url())
    else:
        form = form(user=request.user)
    context['form'] = form
    return render(request, 'events/form.html', context)


def edit(request, pk):
    context = {}

    event = get_object_or_404(Event, pk=pk)
    case = event.case

    case.perm_check(request.user, 'can_add_record')
    context['event'] = event
    context['object'] = case

    form = EventForm.partial(user=request.user, case=case, instance=event)

    if request.method == 'POST':
        form = form(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request,
                _("Success updated event %(event)s") % {'event': obj, })
            return HttpResponseRedirect(case.get_absolute_url())
    else:
        form = form(user=request.user, instance=event)
    context['form'] = form
    return render(request, 'events/form.html', context)


def dismiss(request, pk):  # TODO
    pass


class CalendarListView(PermissionMixin, LoginRequiredMixin, ArchiveIndexView):
    model = Event
    date_field = 'time'
    allow_future = True
    date_list_period = 'month'


class CalendarEventView(PermissionMixin, SelectRelatedMixin, LoginRequiredMixin, MonthArchiveView):
    model = Event
    date_field = "time"
    allow_future = True
    select_related = ['case', 'record']
    template_name = 'events/calendar.html'

    def get_language_code(self):
        return getattr(self.request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)

    def get_context_data(self, **kwargs):
        context = super(CalendarEventView, self).get_context_data(**kwargs)
        locale = (self.get_language_code(), 'utf-8')
        date = (int(self.get_year()), int(self.get_month()))
        cal = EventCalendar(self.object_list, locale=locale).formatmonth(*date)
        context['calendar'] = mark_safe(cal)
        return context


class ICalendarView(KeyAuthMixin, PermissionMixin, BaseListView):
    window = 1
    model = Event

    def get_event(self, obj):
        from icalendar import Event
        event = Event()
        event['uid'] = obj.pk
        event['dtstart'] = obj.time
        event['summary'] = unicode(obj)
        event['description'] = obj.text
        return event

    def get_subcomponents(self):
        return [self.get_event(x) for x in self.get_queryset()]

    def get_icalendar(self):
        from icalendar import Calendar
        cal = Calendar()
        cal['summary'] = 'Events for %s'.format(self.request.user)
        cal['dtstart'] = self.get_start()
        cal['dtend'] = self.get_end()

        [cal.add_component(component) for component in self.get_subcomponents()]
        return cal

    def get_start(self):
        return now() + relativedelta(months=+self.window)

    def get_end(self):
        return now() + relativedelta(months=-self.window)

    def get_queryset(self):
        qs = super(ICalendarView, self).get_queryset()
        qs = qs.filter(time__lt=self.get_start())
        qs = qs.filter(time__gt=self.get_end())
        return qs

    def render_to_response(self, *args, **kwargs):
        response = HttpResponse(content_type='application/force-download')
        response['Content-Disposition'] = 'attachment; filename=calendar.ics'
        response.write(self.get_icalendar().to_ical())
        return response
