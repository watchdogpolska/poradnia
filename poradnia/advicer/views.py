from ajax_datatable import AjaxDatatableView
from atom.ext.crispy_forms.views import FormSetMixin
from atom.views import ActionMessageMixin, ActionView, FormInitialMixin
from braces.views import (
    FormValidMessageMixin,
    LoginRequiredMixin,
    SelectRelatedMixin,
    StaffuserRequiredMixin,
    UserFormKwargsMixin,
)
from dal import autocomplete
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView
from django_filters.views import FilterView

from poradnia.cases.models import Case
from poradnia.users.utils import PermissionMixin
from poradnia.utils.mixins import ExprAutocompleteMixin

from .filters import AdviceFilter
from .forms import AdviceForm, AttachmentForm
from .models import Advice, Area, Attachment, Issue

ORDERING_TEXT = _("Ordering")


class VisibleMixin:
    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.visible()


class AdviceList(
    StaffuserRequiredMixin,
    PermissionMixin,
    SelectRelatedMixin,
    VisibleMixin,
    FilterView,
):
    model = Advice
    filterset_class = AdviceFilter
    select_related = [
        "person_kind",
        "created_by",
        "advicer",
        "institution_kind",
        "case__client",
    ]
    paginate_by = 25
    raise_exception = True


class AdviceTableView(PermissionMixin, TemplateView):
    """
    View for displaying template with Advices table.
    """

    template_name = "advicer/advice_table.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["header_label"] = mark_safe(_("Advice search table"))
        context["ajax_datatable_url"] = reverse("advicer:advice_table_ajax_data")
        return context


class AdviceAjaxDatatableView(PermissionMixin, AjaxDatatableView):
    """
    View to provide table list of all Advices with ajax data.
    """

    model = Advice
    title = "Advices"
    initial_order = [
        ["created_on_str", "desc"],
    ]
    length_menu = [[20, 50, 100], [20, 50, 100]]

    column_defs = [
        {
            "name": "created_on_str",
            "visible": True,
            "title": _("Created on"),
        },
        {
            "name": "subject",
            "visible": True,
            "title": _("Subject"),
        },
        {
            "name": "case_name",
            "visible": True,
            "title": (_("Case") + " - " + _("Subject")),
        },
        {
            "name": "person_kind_name",
            "visible": True,
            "title": _("Type of person who reporting the advice"),
        },
        {
            "name": "institution_kind_name",
            "visible": True,
            "title": _("Institution kind"),
        },
        {
            "name": "advicer_str",
            "visible": True,
            "title": _("Advicer"),
        },
        {
            "name": "grant_on_str",
            "visible": True,
            "title": _("Grant on"),
        },
        {
            "name": "helped_str",
            "visible": True,
            "title": _("We helped?"),
        },
        {
            "name": "visible_str",
            "visible": True,
            "title": _("Visible"),
        },
        {
            "name": "jst_name",
            "visible": True,
            "title": _("Unit of administrative division"),
        },
    ]

    def customize_row(self, row, obj):
        row["subject"] = obj.render_advice_link()
        row["case_name"] = obj.case.render_case_link()
        return

    def get_initial_queryset(self, request=None):
        qs = super().get_initial_queryset(request).select_related()
        return (
            qs.for_user(user=self.request.user)
            .with_formatted_created_on()
            .with_case_name()
            .with_person_kind_name()
            .with_institution_kind_name()
            .with_advicer_str()
            .with_formatted_grant_on()
            .with_helped_str()
            .with_visible_str()
            .with_jst_name_str()
        )


class AdviceUpdate(
    StaffuserRequiredMixin,
    FormSetMixin,
    PermissionMixin,
    FormValidMessageMixin,
    UserFormKwargsMixin,
    VisibleMixin,
    UpdateView,
):
    model = Advice
    form_class = AdviceForm
    inline_model = Attachment
    inline_form_cls = AttachmentForm
    raise_exception = True

    def get_form_valid_message(self):
        return _("{0} updated!").format(self.object)

    def get_instance(self):
        return self.object


class AdviceCreate(
    StaffuserRequiredMixin,
    FormSetMixin,
    FormInitialMixin,
    UserFormKwargsMixin,
    LoginRequiredMixin,
    CreateView,
):
    model = Advice
    form_class = AdviceForm
    inline_model = Attachment
    inline_form_cls = AttachmentForm
    raise_exception = True

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        if "case" in self.request.GET.dict():
            case = get_object_or_404(
                Case.objects.for_user(self.request.user), pk=self.request.GET["case"]
            )
            advicer = case.get_users_with_perms().filter(is_staff=True).first()
            initial["advicer"] = advicer
        return initial


class AdviceDelete(
    StaffuserRequiredMixin,
    PermissionMixin,
    ActionView,
    VisibleMixin,
    ActionMessageMixin,
):
    model = Advice
    success_url = reverse_lazy("advicer:list")
    success_message = _("{subject} deleted!")
    template_name_suffix = "_confirm_delete"
    raise_exception = True

    def action(self):
        Advice.objects.filter(pk=self.object.pk).update(visible=False)


class AdviceDetail(StaffuserRequiredMixin, PermissionMixin, VisibleMixin, DetailView):
    model = Advice
    raise_exception = True


class IssueAutocomplete(
    StaffuserRequiredMixin, ExprAutocompleteMixin, autocomplete.Select2QuerySetView
):
    model = Issue
    search_expr = [
        "name__icontains",
    ]


class AreaAutocomplete(
    StaffuserRequiredMixin, ExprAutocompleteMixin, autocomplete.Select2QuerySetView
):
    model = Area
    search_expr = [
        "name__icontains",
    ]
