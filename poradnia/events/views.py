import locale
from atom.ext.guardian.views import RaisePermissionRequiredMixin

from braces.views import (
    FormValidMessageMixin,
    LoginRequiredMixin,
    SelectRelatedMixin,
    UserFormKwargsMixin,
)
from cached_property import cached_property
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_text
from django.utils.html import mark_safe
from django.utils.timezone import now
from django.utils.translation import ugettext as _
from django.views.generic import (
    ArchiveIndexView,
    CreateView,
    MonthArchiveView,
    UpdateView,
)
from django.views.generic.list import BaseListView

from poradnia.cases.models import Case
from poradnia.keys.mixins import KeyAuthMixin
from poradnia.users.utils import PermissionMixin

from .forms import EventForm
from .models import Event
from .utils import EventCalendar


class EventCreateView(
    RaisePermissionRequiredMixin, UserFormKwargsMixin, FormValidMessageMixin, CreateView
):
    model = Event
    form_class = EventForm
    template_name = "events/form.html"
    permission_required = ["cases.can_add_record"]

    @cached_property
    def case(self):
        return get_object_or_404(Case, pk=self.kwargs["case_pk"])

    def get_permission_object(self):
        return self.case

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs()
        kwargs["case"] = self.case
        return kwargs

    def get_form_valid_message(self):
        return _("Success added new event %(event)s") % ({"event": self.object})


class EventUpdateView(
    RaisePermissionRequiredMixin, UserFormKwargsMixin, FormValidMessageMixin, UpdateView
):
    model = Event
    form_class = EventForm
    template_name = "events/form.html"
    permission_required = ["cases.can_add_record"]

    def get_permission_object(self):
        return self._object.case

    @cached_property
    def _object(self):
        return super().get_object()

    def get_object(self, *args, **kwargs):
        return self._object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["case"] = self.object.case
        return kwargs

    def form_valid(self, form):
        self.object.reminder_set.all().update(active=False)
        return super().form_valid(form)

    def get_form_valid_message(self):
        return _("Success updated event %(event)s") % {"event": self.object}


class CalendarListView(PermissionMixin, LoginRequiredMixin, ArchiveIndexView):
    model = Event
    date_field = "time"
    allow_future = True
    date_list_period = "month"


class CalendarEventView(
    PermissionMixin, SelectRelatedMixin, LoginRequiredMixin, MonthArchiveView
):
    model = Event
    date_field = "time"
    allow_future = True
    select_related = ["case", "record"]
    template_name = "events/calendar.html"

    def get_language_code(self):
        return getattr(self.request, "LANGUAGE_CODE", settings.LANGUAGE_CODE)

    def get_user_locale(self):
        if self.get_language_code() in locale.locale_alias:
            name = locale.locale_alias[self.get_language_code()].split(".")[0]
            return (name, "UTF-8")
        else:
            return locale.getlocale()

    def get_calendar(self):
        date = (int(self.get_year()), int(self.get_month()))
        cal = EventCalendar(self.object_list).formatmonth(*date)
        return mark_safe(cal)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["calendar"] = self.get_calendar()
        return context


class ICalendarView(KeyAuthMixin, PermissionMixin, BaseListView):
    window = 1
    model = Event

    def get_event(self, obj):
        from icalendar import Event

        event = Event()
        event["uid"] = obj.pk
        event["dtstart"] = obj.time
        event["summary"] = force_text(obj)
        event["description"] = obj.text
        return event

    def get_subcomponents(self):
        return [self.get_event(x) for x in self.get_queryset()]

    def get_icalendar(self):
        from icalendar import Calendar

        cal = Calendar()
        cal["summary"] = "Events for {}".format(self.request.user)
        cal["dtstart"] = self.get_start()
        cal["dtend"] = self.get_end()

        for component in self.get_subcomponents():
            cal.add_component(component)
        return cal

    def get_start(self):
        return now() + relativedelta(months=+self.window)

    def get_end(self):
        return now() + relativedelta(months=-self.window)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(time__lt=self.get_start())
        qs = qs.filter(time__gt=self.get_end())
        return qs

    def render_to_response(self, *args, **kwargs):
        response = HttpResponse(content_type="application/force-download")
        response["Content-Disposition"] = "attachment; filename=calendar.ics"
        response.write(self.get_icalendar().to_ical())
        return response
