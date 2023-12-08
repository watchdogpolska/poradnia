from collections import OrderedDict

from ajax_datatable import AjaxDatatableView
from atom.ext.guardian.views import RaisePermissionRequiredMixin
from braces.views import SelectRelatedMixin, UserFormKwargsMixin
from dal import autocomplete
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.views.generic import TemplateView, UpdateView
from django.views.generic.detail import DetailView
from django_filters.views import FilterView

from poradnia.cases.filters import StaffCaseFilter, UserCaseFilter
from poradnia.cases.forms import (
    CaseCloseForm,
    CaseForm,
    CaseGroupPermissionForm,
    CaseMergeForm,
)
from poradnia.cases.models import Case, PermissionGroup
from poradnia.events.forms import EventForm
from poradnia.judgements.views import CourtCaseForm
from poradnia.letters.forms import AddLetterForm
from poradnia.letters.helpers import AttachmentFormSet
from poradnia.records.models import Record
from poradnia.users.views import PermissionMixin


class SingleObjectPermissionMixin(RaisePermissionRequiredMixin):
    def get_permission_object(self):
        return self.object

    @cached_property
    def object(self):
        return super().get_object(self.get_queryset())

    def get_object(self, queryset=None):
        return self.object


class CaseDetailView(SingleObjectPermissionMixin, SelectRelatedMixin, DetailView):
    template_name = "cases/case_detail.html"
    model = Case
    select_related = ["created_by", "modified_by", "advice", "deadline"]
    select_record_related = [
        "letter__created_by",
        "letter",
        "letter__modified_by",
        "event__created_by",
        "event",
        "event__modified_by",
        "event",
    ]
    prefetch_record_related = ["letter__attachment_set"]
    permission_required = ["cases.can_view"]
    accept_global_perms = True

    def get_record_list(self):
        return (
            Record.objects.filter(case=self.object)
            .for_user(self.request.user)
            .select_related(*self.select_record_related)
            .prefetch_related(*self.prefetch_record_related)
            .all()
        )

    def get_forms(self):
        forms = OrderedDict()
        forms["letter"] = {
            "title": _("Letter"),
            "form": AddLetterForm(user=self.request.user, case=self.object),
            "formset": AttachmentFormSet(instance=None),
        }
        if self.request.user.is_staff:
            forms["event"] = {
                "title": _("Event"),
                "form": EventForm(user=self.request.user, case=self.object),
            }
        forms["court"] = {
            "title": _("Court Case"),
            "form": CourtCaseForm(user=self.request.user, case=self.object),
        }
        return forms

    def get_next_and_prev(self):
        # Get next or prev objects
        try:
            next = self.object.get_next_for_user(self.request.user)
        except Case.DoesNotExist:
            next = None

        # Get next or prev objects
        try:
            previous = self.object.get_prev_for_user(self.request.user)
        except Case.DoesNotExist:
            previous = None
        return next, previous

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["forms"] = self.get_forms()
        context["record_list"] = self.get_record_list()
        context["casegroup_form"] = CaseGroupPermissionForm(
            case=self.object, user=self.request.user
        )
        context["permissions_help_text"] = "\n".join(
            [group.group_help_text for group in PermissionGroup.objects.all()]
        )
        context["next"], context["previous"] = self.get_next_and_prev()
        return context


class CaseListView(PermissionMixin, SelectRelatedMixin, FilterView):
    model = Case
    paginate_by = 25
    select_related = ["client"]

    def get_filterset_class(self, *args, **kwargs):
        return StaffCaseFilter if self.request.user.is_staff else UserCaseFilter

    def get_filterset_kwargs(self, *args, **kwargs):
        kw = super().get_filterset_kwargs(*args, **kwargs)
        kw["user"] = self.request.user
        return kw

    def get_queryset(self, *args, **kwargs):  # TODO: Mixins
        qs = super().get_queryset(*args, **kwargs)
        if self.request.user.is_staff:
            qs = qs.with_involved_staff()
        if self.request.user.is_staff:
            qs = qs.with_advice_status()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = Case.STATUS
        return context


class CaseTableView(PermissionMixin, TemplateView):
    """
    View for displaying template with Cases table.
    """

    template_name = "cases/case_table.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["header_label"] = mark_safe(_("Cases search table"))
        context["ajax_datatable_url"] = reverse("cases:case_table_ajax_data")
        context["statuses"] = Case.STATUS
        context["involved_staff"] = [
            (None, _("All")),
        ] + list(Case.objects.involved_staff().values_list("id", "nicename"))
        return context


class CaseAjaxDatatableView(PermissionMixin, AjaxDatatableView):
    """
    View to provide table list of all Cases with ajax data.
    """

    model = Case
    title = "Cases"
    initial_order = [
        ["id", "desc"],
    ]
    length_menu = [[200, 20, 50, 100], [200, 20, 50, 100]]
    search_values_separator = "|"

    column_defs = [
        {
            "name": "id",
            "visible": True,
            "title": _("Number"),
        },
        {
            "name": "status",
            "visible": True,
            "searchable": False,
            "orderable": False,
            "title": _("S"),
        },
        {
            "name": "name",
            "visible": True,
            "title": _("Subject"),
        },
        {
            "name": "handled",
            "visible": False,  # needded to speed up calculation of other columns
            "searchable": False,
            "orderable": False,
            "title": _("Handled"),
        },
        {
            "name": "has_project",
            "visible": True,
            "searchable": False,
            "orderable": False,
            "title": _("Project"),
        },
        {
            "name": "involved_staff",
            "title": _("Involved staff"),
            "placeholder": True,
            "searchable": False,
            "orderable": False,
            "className": "highlighted",
        },
        {
            "name": "deadline_str",
            "visible": True,
            "title": _("Deadline date"),
        },
        {
            "name": "client_pretty_name",
            "visible": True,
            "title": _("Client"),
        },
        {
            "name": "last_action_str",
            "visible": True,
            "title": _("Last action"),
            "width": 80,
        },
        {
            "name": "advice_subject",
            "visible": True,
            "foreign_field": "advice__subject",
            "searchable": True,
            "orderable": True,
            "title": (_("Advice") + " - " + _("Subject")),
        },
        {
            "name": "letter_count",
            "visible": True,
            "searchable": False,
            "orderable": True,
            "title": _("Letter count"),
        },
        {
            "name": "created_on_str",
            "visible": True,
            "title": _("Created on"),
            "width": 80,
        },
    ]

    def customize_row(self, row, obj):
        row["name"] = obj.render_case_link()
        # row["name"] = obj.render_case_link_formatted(self.request.user)
        row["has_project"] = obj.render_project_badge()
        row["status"] = obj.render_status()
        # row["handled"] = obj.render_handled()
        row["involved_staff"] = obj.render_involved_staff()
        row["deadline_str"] = (
            f"""<span class="label label-warning">
            <i class="fa fa-fire"></i>{obj.deadline_str[:10]}</span>"""
            if obj.deadline_str
            else ""
        )
        try:
            row["advice_subject"] = obj.advice.render_advice_link()
        except Case.advice.RelatedObjectDoesNotExist:
            row["advice_subject"] = ""
        return

    def get_initial_queryset(self, request=None):
        qs = super().get_initial_queryset(request)
        qs = qs.ajax_status_filter(self.request)
        qs = qs.ajax_boolean_filter(self.request, "handled_", "handled")
        qs = qs.ajax_boolean_filter(self.request, "has_project_", "has_project")
        qs = qs.ajax_has_deadline_filter(self.request)
        qs = qs.ajax_involved_staff_filter(self.request)
        return (
            qs.for_user(user=self.request.user)
            .with_involved_staff()
            .with_formatted_datetime("created_on", timezone.get_default_timezone())
            .with_formatted_datetime("last_action", timezone.get_default_timezone())
            .with_formatted_deadline()
            .with_user_pretty_name_str("client")
        )


class CaseUpdateView(UserFormKwargsMixin, SingleObjectPermissionMixin, UpdateView):
    form_class = CaseForm
    template_name = "cases/case_form.html"
    model = Case
    permission_required = ["cases.can_change_case"]

    def form_valid(self, form):
        obj = form.save()
        messages.success(
            self.request, _('Successful updated "%(object)s".') % {"object": obj}
        )
        return redirect(obj)


class CaseCloseView(RaisePermissionRequiredMixin, UserFormKwargsMixin, UpdateView):
    form_class = CaseCloseForm
    permission_required = ["cases.can_close_case"]
    template_name = "cases/case_close.html"
    model = Case

    def form_valid(self, form):
        obj = form.save()
        messages.success(
            self.request, _('Successfully closed "%(object)s".') % {"object": obj}
        )
        return redirect(obj)


class CaseMergeView(RaisePermissionRequiredMixin, UserFormKwargsMixin, UpdateView):
    form_class = CaseMergeForm
    permission_required = ["cases.can_merge_case"]
    template_name = "cases/case_merge.html"
    model = Case

    def form_valid(self, form):
        obj = form.save()
        messages.success(
            self.request, _('Successfully merged "%(object)s".') % {"object": obj}
        )
        return redirect(obj)


class CaseAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Case.objects.for_user(self.request.user).all()

        if self.q:
            q = Q(name__icontains=self.q)
            if self.q.isnumeric():
                q = q | Q(pk=self.q)
            qs = qs.filter(q)
        return qs
