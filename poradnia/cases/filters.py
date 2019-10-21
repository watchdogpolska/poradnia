from atom.ext.django_filters.filters import CrispyFilterMixin
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
import django_filters

from poradnia.users.filters import UserChoiceFilter

from .models import Case


class NullDateRangeFilter(django_filters.DateRangeFilter):
    def __init__(self, none_label=None, *args, **kwargs):
        self.options[6] = (
            none_label or _("None"),
            lambda qs, name: qs.filter(**{"%s__isnull" % name: True}),
        )
        super(NullDateRangeFilter, self).__init__(*args, **kwargs)


class CaseFilterMixin(object):
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(CaseFilterMixin, self).__init__(*args, **kwargs)


class PermissionChoiceFilter(django_filters.ModelChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs.update(
            dict(
                label=_("Has access by"),
                method=lambda qs, _, v: qs.for_assign(v),
                queryset=get_user_model().objects.filter(is_staff=True).all(),
            )
        )
        super(PermissionChoiceFilter, self).__init__(*args, **kwargs)


class StaffCaseFilter(CrispyFilterMixin, CaseFilterMixin, django_filters.FilterSet):
    name = django_filters.CharFilter(label=_("Subject"), lookup_expr="icontains")
    client = UserChoiceFilter(label=_("Client"))
    permission = PermissionChoiceFilter()
    handled = django_filters.BooleanFilter(label=_("Replied"))
    status = django_filters.MultipleChoiceFilter(label=_("Status"), choices=Case.STATUS)
    has_advice = django_filters.BooleanFilter(label=("Advice registered"))
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
        super(StaffCaseFilter, self).__init__(*args, **kwargs)

    @property
    def form(self):
        form = super(StaffCaseFilter, self).form
        form.helper.include_media = False
        return form

    class Meta:
        model = Case
        fields = ["id", "status", "client", "name", "has_project"]


class UserCaseFilter(CrispyFilterMixin, CaseFilterMixin, django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        kwargs["queryset"] = kwargs.pop("queryset").order_by(
            "-%s" % (Case.USER_ORDER_DEFAULT_FIELD)
        )
        super(UserCaseFilter, self).__init__(*args, **kwargs)

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
