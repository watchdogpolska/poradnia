from django.utils.html import mark_safe
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.views.generic import MonthArchiveView, ArchiveIndexView
from braces.views import SelectRelatedMixin
from cases.models import Case
from users.mixins import PermissionMixin
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


class CalendarListView(PermissionMixin, ArchiveIndexView):
    model = Event
    date_field = 'time'
    allow_future = True
    date_list_period = 'month'


class CalendarEventView(PermissionMixin, SelectRelatedMixin, MonthArchiveView):
    model = Event
    date_field = "time"
    allow_future = True
    select_related = ['case', 'record']
    template_name = 'events/calendar.html'

    def get_context_data(self, **kwargs):
        context = super(CalendarEventView, self).get_context_data(**kwargs)
        cal = EventCalendar(self.object_list).formatmonth(int(self.get_year()), int(self.get_month()))
        context['calendar'] = mark_safe(cal)
        return context
