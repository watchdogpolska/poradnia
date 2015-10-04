import django_filters
from django.utils.translation import ugettext as _

from atom.filters import CrispyFilterMixin
from users.filters import UserChoiceFilter

from .models import Case


class NullDateRangeFilter(django_filters.DateRangeFilter):
    def __init__(self, none_label=None, *args, **kwargs):
        if not none_label:
            none_label = _('None')
        self.options[6] = (none_label,
                           lambda qs, name: qs.filter(**{"%s__isnull" % name: True})
                           )
        super(NullDateRangeFilter, self).__init__(*args, **kwargs)


class CaseFilterMixin(object):
    def __init__(self, *args, **kwargs):
        super(CaseFilterMixin, self).__init__(*args, **kwargs)
        self.filters['status'].field.choices.insert(0, ('', u'---------'))


class StaffCaseFilter(CrispyFilterMixin, CaseFilterMixin, django_filters.FilterSet):
    name = django_filters.CharFilter(label=_("Subject"), lookup_type='icontains')
    client = UserChoiceFilter(label=_("Client"))
    created_by = UserChoiceFilter(label=_("Created by"))
    created_on = django_filters.DateRangeFilter(label=_("Created on"))
    last_send = NullDateRangeFilter(label=_("Last send"), none_label=_("No reply"))
    last_action = django_filters.DateRangeFilter(label=_("Last action"))
    handled = django_filters.BooleanFilter(label=_("Handled?"))

    def get_order_by(self, order_choice):
        if order_choice == 'default':
            return ['-deadline', 'status', '-last_send', '-last_action']
        return super(StaffCaseFilter, self).get_order_by(order_choice)

    class Meta:
        model = Case
        fields = ['status', 'client', 'name', 'created_on', 'last_send', 'last_action']
        order_by = (
            ('default', _('Default')),
            ('deadline', _('Dead-line')),
            ('pk', _('ID')),
            ('client', _('Client')),
            ('created_on', _('Created on')),
            ('last_send', _('Last send')),
            ('last_action', _('Last action')),
        )


class UserCaseFilter(CrispyFilterMixin, CaseFilterMixin, django_filters.FilterSet):
    name = django_filters.CharFilter(label=_("Subject"), lookup_type='icontains')
    created_on = django_filters.DateRangeFilter(label=_("Created on"))
    last_send = django_filters.DateRangeFilter(label=_("Last send"))

    class Meta:
        model = Case
        fields = ['status', 'name', 'created_on', 'last_send']
        order_by = (
            ('default', _('Default')),
            ('pk', _('ID')),
            ('Client', _('Client')),
            ('created_on', _('Created on')),
            ('last_send', _('Last send')),
        )

    def get_order_by(self, order_choice):
        if order_choice == 'default':
            return ['-last_send']
        return [order_choice]
