import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from poradnia.users.filters import UserChoiceFilter
from poradnia.utils.mixins import CrispyApplyFilterMixin

from .models import Case


class StaffCaseFilterFormHelper(FormHelper):
    """Multi-column horizontal layout for the staff cases list filter.

    Restores the dense BS3-era arrangement; without an explicit Layout,
    crispy_forms BS5 stacks each field full-width which produced a ~9-row
    vertical filter on `/sprawy/`.
    """

    form_method = "get"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = Layout(
            Row(
                Column("id", css_class="col-md-2"),
                Column("status", css_class="col-md-3"),
                Column("client", css_class="col-md-3"),
                Column("name", css_class="col-md-4"),
            ),
            Row(
                Column("has_project", css_class="col-md-3"),
                Column("permission", css_class="col-md-3"),
                Column("handled", css_class="col-md-3"),
                Column("has_advice", css_class="col-md-3"),
            ),
            Row(
                Column("o", css_class="col-md-4"),
                Column(
                    Submit("filter", _("Apply Filter"), css_class="btn-danger"),
                    css_class="col-md-3 align-self-end",
                ),
            ),
        )


class UserCaseFilterFormHelper(FormHelper):
    """Compact horizontal layout for the client cases list filter."""

    form_method = "get"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = Layout(
            Row(
                Column("name", css_class="col-md-4"),
                Column("created_on", css_class="col-md-3"),
                Column("last_send", css_class="col-md-3"),
            ),
            Row(
                Column("o", css_class="col-md-4"),
                Column(
                    Submit("filter", _("Apply Filter"), css_class="btn-danger"),
                    css_class="col-md-3 align-self-end",
                ),
            ),
        )


class NullDateRangeFilter(django_filters.DateRangeFilter):
    def __init__(self, none_label=None, *args, **kwargs):
        self.options[6] = (
            none_label or _("None"),
            lambda qs, name: qs.filter(**{"%s__isnull" % name: True}),
        )
        super().__init__(*args, **kwargs)


class CaseFilterMixin:
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)


class PermissionChoiceFilter(django_filters.ModelChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs.update(
            dict(
                label=_("Has access by"),
                method=lambda qs, _, v: qs.for_assign(v),
                queryset=get_user_model().objects.filter(is_staff=True).all(),
            )
        )
        super().__init__(*args, **kwargs)


class StaffCaseFilter(
    CrispyApplyFilterMixin, CaseFilterMixin, django_filters.FilterSet
):
    name = django_filters.CharFilter(label=_("Subject"), lookup_expr="icontains")
    client = UserChoiceFilter(label=_("Client"))
    permission = PermissionChoiceFilter()
    handled = django_filters.BooleanFilter(label=_("Replied"))
    status = django_filters.MultipleChoiceFilter(label=_("Status"), choices=Case.STATUS)
    has_advice = django_filters.BooleanFilter(label=_("Advice registered/tagged"))
    o = django_filters.OrderingFilter(
        fields=[
            "last_action",
            "deadline",
            "pk",
            "client",
            "created_on",
            "last_send",
            "last_action",
            "last_received",
        ],
        initial="last_action",
        help_text=None,
        field_labels={
            "deadline": _("Dead-line"),
            "pk": _("ID"),
            "client": _("Client"),
            "created_on": _("Created on"),
            "last_send": _("Last send"),
            "last_action": _("Default"),
            "last_received": _("Last received"),
        },
    )

    def __init__(self, *args, **kwargs):
        kwargs["queryset"] = kwargs.pop("queryset").order_by(
            "-%s" % (Case.STAFF_ORDER_DEFAULT_FIELD)
        )
        super().__init__(*args, **kwargs)

    @property
    def form(self):
        form = super().form
        form.helper = StaffCaseFilterFormHelper(form)
        form.helper.include_media = True
        return form

    class Meta:
        model = Case
        fields = ["id", "status", "client", "name", "has_project"]


class UserCaseFilter(CrispyApplyFilterMixin, CaseFilterMixin, django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        kwargs["queryset"] = kwargs.pop("queryset").order_by(
            "-%s" % (Case.USER_ORDER_DEFAULT_FIELD)
        )
        super().__init__(*args, **kwargs)

    @property
    def form(self):
        form = super().form
        form.helper = UserCaseFilterFormHelper(form)
        return form

    name = django_filters.CharFilter(label=_("Subject"), lookup_expr="icontains")
    created_on = django_filters.DateRangeFilter(label=_("Created on"))
    last_send = django_filters.DateRangeFilter(label=_("Last send"))
    o = django_filters.OrderingFilter(
        fields=["last_send", "pk", "created_on"],
        help_text=None,
        initial="last_send",
        field_labels={
            "last_send": _("Last send"),
            "pk": _("ID"),
            "created_on": _("Created on"),
        },
    )

    class Meta:
        model = Case
        fields = ["name", "created_on", "last_send"]
        order_by_field = "last_send"
