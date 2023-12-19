import locale

from ajax_datatable import AjaxDatatableView
from atom.ext.guardian.views import RaisePermissionRequiredMixin
from braces.views import (
    FormValidMessageMixin,
    LoginRequiredMixin,
    SelectRelatedMixin,
    UserFormKwargsMixin,
)
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import gettext as _
from django.views.generic import (
    ArchiveIndexView,
    CreateView,
    MonthArchiveView,
    TemplateView,
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

    def form_valid(self, form):
        response = super().form_valid(form)
        content_type = ContentType.objects.get_for_model(Event)
        change_dict = {
            "changed": form.changed_data,
            "cleaned_data": form.cleaned_data,
        }
        LogEntry.objects.log_action(
            user_id=self.request.user.id,
            content_type_id=content_type.id,
            object_id=self.object.id,
            object_repr=force_str(self.object),
            action_flag=ADDITION,
            change_message=f"{change_dict}",
        )
        return response

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
        content_type = ContentType.objects.get_for_model(Event)
        change_dict = {
            "changed": form.changed_data,
            "cleaned_data": form.cleaned_data,
        }
        LogEntry.objects.log_action(
            user_id=self.request.user.id,
            content_type_id=content_type.id,
            object_id=self.object.id,
            object_repr=str(self.object),
            action_flag=CHANGE,
            change_message=f"{change_dict}",
        )
        return super().form_valid(form)

    def get_form_valid_message(self):
        return _("Success updated event %(event)s") % {"event": self.object}


class CalendarListView(PermissionMixin, LoginRequiredMixin, ArchiveIndexView):
    model = Event
    date_field = "time"
    allow_future = True
    date_list_period = "month"


class EventTableView(PermissionMixin, TemplateView):
    """
    View for displaying template with Events table.
    """

    template_name = "events/events_table.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["header_label"] = mark_safe(_("Events search table"))
        context["ajax_datatable_url"] = reverse("events:events_table_ajax_data")
        return context


class EventAjaxDatatableView(PermissionMixin, AjaxDatatableView):
    """
    View to provide table list of all Events with ajax data.
    """

    model = Event
    title = "Events"
    initial_order = [
        ["time", "desc"],
    ]
    length_menu = [[20, 50, 100], [20, 50, 100]]
    search_values_separator = "|"
    show_date_filters = True

    column_defs = [
        {
            "name": "time",
            "visible": True,
            "searchable": False,
            "orderable": True,
            "title": _("Time"),
        },
        {
            "name": "text",
            "visible": True,
            "title": _("Subject"),
            "width": "300",
        },
        {
            "name": "case_name",
            "visible": True,
            "foreign_field": "case__name",
            "defaultContent": "",
            "title": (_("Case") + " - " + _("Subject")),
        },
        {
            "name": "case_client",
            "visible": True,
            "foreign_field": "case__client__nicename",
            "defaultContent": "",
            "title": _("Client"),
        },
        {
            "name": "properties",
            # TODO: check why translation doesn't work
            # "title": _("Properties..."),
            "title": "Właściwości",
            "placeholder": True,
            "searchable": False,
            "orderable": False,
            # "className": "highlighted",
        },
        {
            "name": "court_case",
            "visible": True,
            "foreign_field": "courtsession__courtcase__signature",
            "defaultContent": "",
            "title": _("Court case"),
            "searchable": True,
            "orderable": True,
        },
        {
            "name": "court",
            "visible": True,
            "foreign_field": "courtsession__courtcase__court__name",
            "defaultContent": "",
            "title": _("Court"),
            "searchable": True,
            "orderable": True,
        },
    ]

    def customize_row(self, row, obj):
        row["case_name"] = obj.case.render_case_link() if obj.case else ""
        row["text"] = obj.render_event_link
        row["properties"] = obj.render_property_icons
        row["court_case"] = obj.render_court_case
        if obj.time:
            row["time"] = obj.render_time
        else:
            row["time"] = ""

    def get_initial_queryset(self, request=None):
        qs = super().get_initial_queryset(request)
        qs = qs.ajax_boolean_filter(self.request, "deadline_", "deadline")
        qs = qs.ajax_boolean_filter(self.request, "completed_", "completed")
        qs = qs.ajax_boolean_filter(self.request, "public_", "public")
        qs = qs.courtsession_filter(self.request)
        return qs

    def get_latest_by(self, request):
        return "record_max"


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

    def get_allow_empty(self):
        """
        Return ``True`` if the view should display empty lists and ``False``
        if a 404 should be raised instead.
        """
        return True


class ICalendarView(KeyAuthMixin, PermissionMixin, BaseListView):
    window = 1
    model = Event

    def get_event(self, obj):
        from icalendar import Event

        event = Event()
        event["uid"] = obj.pk
        event["dtstart"] = obj.time
        event["summary"] = force_str(obj)
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
