try:
    from urllib.parse import urlencode
except:
    from urllib import urlencode  # noqa

import autocomplete_light
from django.contrib.auth import get_user_model
from django_filters import ModelChoiceFilter
import django_filters
from atom.filters import CrispyFilterMixin
from users.models import User


class UserChoiceFilter(ModelChoiceFilter):
    def __init__(self, queryset=None, widget=None, *args, **kwargs):
        widget = widget or autocomplete_light.ChoiceWidget('UserAutocomplete')
        queryset = queryset or get_user_model().objects.all()
        super(UserChoiceFilter, self).__init__(queryset=queryset, widget=widget, *args, **kwargs)


class UserFilter(CrispyFilterMixin, django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super(UserFilter, self).__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ['is_superuser', ]
