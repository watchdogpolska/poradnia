from atom.ext.django_filters.filters import CrispyFilterMixin
from dal import autocomplete
from django.contrib.auth import get_user_model
import django_filters

from poradnia.users.models import User

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode  # noqa


class UserChoiceFilter(django_filters.ModelChoiceFilter):
    def __init__(self, queryset=None, widget=None, *args, **kwargs):
        widget = widget or autocomplete.ModelSelect2(url="users:autocomplete")
        queryset = queryset or get_user_model().objects.all()
        super().__init__(queryset=queryset, widget=widget, *args, **kwargs)


class UserFilter(CrispyFilterMixin, django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ["is_superuser"]
