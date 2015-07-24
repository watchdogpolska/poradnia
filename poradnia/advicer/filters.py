from django.utils.translation import ugettext_lazy as _
import django_filters
from utilities.filters import CrispyFilterMixin
from users.filters import UserChoiceFilter
from .models import Advice


class AdviceFilter(CrispyFilterMixin, django_filters.FilterSet):
    advicer = UserChoiceFilter(label=_("Advicer"))
    created_by = UserChoiceFilter(label=_("Created by"))
    created_on = django_filters.DateRangeFilter(label=_("Created on"))

    class Meta:
        model = Advice
        fields = ['advicer', 'created_by', 'created_on', 'person_kind']
