from ajax_datatable import AjaxDatatableView
from atom.views import ActionMessageMixin, ActionView, FormInitialMixin
from braces.views import (
    FormValidMessageMixin,
    LoginRequiredMixin,
    SelectRelatedMixin,
    StaffuserRequiredMixin,
    UserFormKwargsMixin,
)
from dal import autocomplete
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin
from django_filters.views import FilterView

from poradnia.cases.models import Case
from poradnia.users.models import User
from poradnia.users.utils import PermissionMixin
from poradnia.utils.mixins import ExprAutocompleteMixin
from poradnia.utils.utils import get_numeric_param

from .filters import AdviceFilter
from .forms import AdviceForm
from .models import Advice, Area, Issue

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
    search_values_separator = "|"

    column_defs = [
        {
            "name": "created_on_str",
            "visible": True,
            "width": 80,
            "title": _("Created on"),
        },
        {
            "name": "subject",
            "visible": True,
            "title": _("Subject"),
        },
        {
            "name": "comment",
            "visible": True,
            "title": _("Comment"),
        },
        {
            "name": "issues",
            "visible": True,
            "choices": True,
            "autofilter": True,
            "title": _("Thematic scopes of requests"),
            "m2m_foreign_field": "issues__name",
        },
        {
            "name": "area",
            "visible": True,
            "choices": True,
            "autofilter": True,
            "title": _("Problems regarding the right to information"),
            "m2m_foreign_field": "area__name",
        },
        {
            "name": "case_name",
            "visible": True,
            "foreign_field": "case__name",
            "defaultContent": "",
            "title": (_("Case") + " - " + _("Subject")),
        },
        {
            "name": "person_kind_name",
            "visible": True,
            "choices": True,
            "autofilter": True,
            "foreign_field": "person_kind__name",
            "defaultContent": "",
            "title": _("Type of person who reporting the advice"),
        },
        {
            "name": "institution_kind_name",
            "visible": True,
            "choices": True,
            "autofilter": True,
            "foreign_field": "institution_kind__name",
            "defaultContent": "",
            "title": _("Institution kind"),
        },
        {
            "name": "advicer_name",
            "choices": True,
            "autofilter": True,
            "visible": True,
            "foreign_field": "advicer__nicename",
            "title": _("Advicer"),
        },
        {
            "name": "grant_on_str",
            "visible": True,
            "width": 80,
            "title": _("Grant on"),
        },
        {
            "name": "jst_name",
            "visible": True,
            "title": _("Unit of administrative division"),
        },
        {
            "name": "helped",
            "visible": True,
            "searchable": False,
            "orderable": True,
            "title": _("H?"),
        },
        {
            "name": "visible",
            "searchable": False,
            "orderable": True,
            "visible": True,
            "title": _("V."),
        },
    ]

    def customize_row(self, row, obj):
        row["subject"] = obj.render_advice_link()
        row["case_name"] = obj.case.render_case_link() if obj.case else ""
        row["helped"] = obj.render_helped()
        row["visible"] = obj.render_visible()
        return

    def _apply_helped_filter(self, qs):
        helped_filter = []
        for param, value in [("helped_yes", True), ("helped_no", False)]:
            if get_numeric_param(self.request, param):
                helped_filter.append(value)
        if helped_filter:
            helped_query = Q(helped__in=helped_filter)
        else:
            helped_query = Q(helped__isnull=True)
        if get_numeric_param(self.request, "helped_blank"):
            return qs.filter(helped_query | Q(helped__isnull=True))
        return qs.filter(helped_query & Q(helped__isnull=False))

    def _apply_visible_filter(self, qs):
        visble_filter = []
        for param, value in [("visible_yes", True), ("visible_no", False)]:
            if get_numeric_param(self.request, param):
                visble_filter.append(value)
        if visble_filter:
            return qs.filter(visible__in=visble_filter)
        return qs.filter(visible__isnull=True)

    def _apply_nullable_bool_filter(self, qs, param_yes, param_no, field):
        yes = get_numeric_param(self.request, param_yes)
        no = get_numeric_param(self.request, param_no)
        if yes and no:
            return qs
        if yes:
            return qs.filter(**{field: True})
        if no:
            return qs.filter(Q(**{field: False}) | Q(**{f"{field}__isnull": True}))
        return qs.none()

    def get_initial_queryset(self, request=None):
        qs = super().get_initial_queryset(request).select_related().prefetch_related()
        qs = self._apply_helped_filter(qs)
        qs = self._apply_visible_filter(qs)
        qs = self._apply_nullable_bool_filter(
            qs, "interesting_case_yes", "interesting_case_no", "interesting_case"
        )
        qs = self._apply_nullable_bool_filter(
            qs, "for_knowledge_base_yes", "for_knowledge_base_no", "for_knowledge_base"
        )
        qs = qs.with_ai_review_flags()
        qs = self._apply_nullable_bool_filter(
            qs,
            "has_ai_tag_suggestion_yes",
            "has_ai_tag_suggestion_no",
            "has_ai_tag_suggestion",
        )
        qs = self._apply_nullable_bool_filter(
            qs,
            "has_ai_tag_suggestion_to_review_yes",
            "has_ai_tag_suggestion_to_review_no",
            "has_ai_tag_suggestion_to_review",
        )
        return (
            qs.for_user(user=self.request.user)
            .with_formatted_datetime("created_on", timezone.get_default_timezone())
            .with_formatted_datetime("grant_on", timezone.get_default_timezone())
            .with_jst_name_str()
        )

    def get_column_defs(self, request):
        team_choices = set(
            User.objects.filter(is_staff=True)
            .order_by("nicename")
            .values_list("nicename", flat=True)
        )
        updated_choices = set(
            Advice.objects.filter(advicer__isnull=False).values_list(
                "advicer__nicename", flat=True
            )
        ).union(team_choices)
        choices = [(v, v) for v in sorted(updated_choices)]
        for col in self.column_defs:
            if col["name"] == "advicer_name":
                col["choices"] = choices
        return self.column_defs


class AdviceUpdate(
    StaffuserRequiredMixin,
    PermissionMixin,
    FormValidMessageMixin,
    UserFormKwargsMixin,
    VisibleMixin,
    UpdateView,
):
    model = Advice
    form_class = AdviceForm
    raise_exception = True

    def get_form_valid_message(self):
        return _("{0} updated!").format(self.object)


class AdviceCreate(
    StaffuserRequiredMixin,
    FormInitialMixin,
    UserFormKwargsMixin,
    LoginRequiredMixin,
    CreateView,
):
    model = Advice
    form_class = AdviceForm
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

    # added for easy debugging
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class AdviceAiTagsAcceptView(
    StaffuserRequiredMixin, PermissionMixin, VisibleMixin, SingleObjectMixin, View
):
    model = Advice
    raise_exception = True
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        tags_request = self.object.ai_tags_request
        if tags_request is None or not self.object.ai_assistant_tags:
            return render(
                request, "advicer/_ai_suggestion_table.html", {"object": self.object}
            )

        # "comment" is intentionally excluded: it's a human-authored field and
        # must never be overwritten by an AI suggestion.
        tags = self.object.ai_assistant_tags
        applied = {
            "subject": tags.get("subject"),
            "summary": tags.get("summary"),
            "person_kind": tags.get("person_kind"),
            "institution_kind": tags.get("institution_kind"),
            "issues": tags.get("issues") or [],
            "area": tags.get("area") or [],
        }
        if "jst" in tags:
            applied["jst"] = tags["jst"]

        self.object.subject = applied["subject"]
        self.object.summary = applied["summary"]
        self.object.person_kind_id = applied["person_kind"]
        self.object.institution_kind_id = applied["institution_kind"]
        if "jst" in applied:
            self.object.jst_id = applied["jst"]
        self.object.modified_by = request.user
        self.object.save()
        self.object.issues.set(applied["issues"])  # replace, not merge
        self.object.area.set(applied["area"])  # replace, not merge

        tags_request.accepted_by = request.user
        tags_request.accepted_at = timezone.now()
        tags_request.save(update_fields=["accepted_by", "accepted_at", "updated_at"])

        content_type = ContentType.objects.get_for_model(Advice)
        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=content_type.id,
            object_id=self.object.id,
            object_repr=str(self.object),
            action_flag=CHANGE,
            change_message=f"{{'applied_ai_assistant_tags': {applied}}}",
        )
        return render(
            request, "advicer/_ai_suggestion_table.html", {"object": self.object}
        )


class AdviceAiTagsRejectView(
    StaffuserRequiredMixin, PermissionMixin, VisibleMixin, SingleObjectMixin, View
):
    model = Advice
    raise_exception = True
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        reason = (request.POST.get("rejection_reason") or "").strip()
        if not reason:
            return HttpResponseBadRequest("rejection_reason is required")

        tags_request = self.object.ai_tags_request
        if tags_request is not None:
            tags_request.rejected_by = request.user
            tags_request.rejected_at = timezone.now()
            tags_request.rejection_reason = reason
            tags_request.save(
                update_fields=[
                    "rejected_by",
                    "rejected_at",
                    "rejection_reason",
                    "updated_at",
                ]
            )
        # Advice's own fields are intentionally untouched.
        return render(
            request, "advicer/_ai_suggestion_table.html", {"object": self.object}
        )


class IssueAutocomplete(
    StaffuserRequiredMixin, ExprAutocompleteMixin, autocomplete.AlightQuerySetView
):
    model = Issue
    search_expr = [
        "name__icontains",
    ]


class AreaAutocomplete(
    StaffuserRequiredMixin, ExprAutocompleteMixin, autocomplete.AlightQuerySetView
):
    model = Area
    search_expr = [
        "name__icontains",
    ]
