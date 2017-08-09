from atom.ext.django_filters.filters import CrispyFilterMixin
from dal import autocomplete

try:
    from urllib.parse import urlencode
except:
    from urllib import urlencode  # noqa

import django_filters
from django.contrib.auth import get_user_model
from django_filters import ModelChoiceFilter
from poradnia.users.models import User


class UserChoiceFilter(ModelChoiceFilter):
    def __init__(self, queryset=None, widget=None, *args, **kwargs):
        widget = widget or autocomplete.ModelSelect2(url='users:autocomplete')
        queryset = queryset or get_user_model().objects.all()
        super(UserChoiceFilter, self).__init__(queryset=queryset, widget=widget, *args, **kwargs)


class UserFilter(CrispyFilterMixin, django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super(UserFilter, self).__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ['is_superuser', ]
