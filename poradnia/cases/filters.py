import django_filters
from django.utils.translation import ugettext as _
from utilities.filters import CrispyFilterMixin
from users.filters import UserChoiceFilter
from .models import Case


class StaffCaseFilter(CrispyFilterMixin, django_filters.FilterSet):
    name = django_filters.CharFilter(label=_("Subject"), lookup_type='icontains')
    client = UserChoiceFilter(label=_("Client"))
    created_by = UserChoiceFilter(label=_("Created by"))
    created_on = django_filters.DateRangeFilter(label=_("Created on"))
    last_send = django_filters.DateRangeFilter(label=_("Last send"))
    last_action = django_filters.DateRangeFilter(label=_("Last action"))

    class Meta:
        model = Case
        fields = ['status', 'client', 'name', 'created_on', 'last_send', 'last_action']
        order_by = (
            ('deadline', _('Dead-line')),
            ('pk', _('ID')),
            ('client', _('Client')),
            ('created_on', _('Created on')),
            ('last_send', _('Last send')),
        )


class UserCaseFilter(CrispyFilterMixin, django_filters.FilterSet):
    name = django_filters.CharFilter(label=_("Subject"), lookup_type='icontains')
    created_on = django_filters.DateRangeFilter(label=_("Created on"))
    last_send = django_filters.DateRangeFilter(label=_("Last send"))

    class Meta:
        model = Case
        fields = ['status', 'name', 'created_on', 'last_send']
        order_by = (
            ('pk', _('ID')),
            ('Client', _('Client')),
            ('created_on', _('Created on')),
            ('last_send', _('Last send')),
        )
