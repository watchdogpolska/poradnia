import django_filters
from atom.ext.django_filters.filters import CrispyFilterMixin
from crispy_forms.helper import FormHelper
from dal import autocomplete
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from poradnia.users.models import User


class UserChoiceFilter(django_filters.ModelChoiceFilter):
    def __init__(self, queryset=None, widget=None, *args, **kwargs):
        widget = widget or autocomplete.ModelSelect2(url="users:autocomplete")
        queryset = queryset or get_user_model().objects.all()
        super().__init__(queryset=queryset, widget=widget, *args, **kwargs)


class UserFilter(CrispyFilterMixin, django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def form(self):
        self._form = super(CrispyFilterMixin, self).form
        self._form.helper = FormHelper(self._form)
        self._form.helper.form_method = "get"
        self._form.helper.form_class = "form-inline"
        return self._form

    sort = django_filters.OrderingFilter(
        fields=(
            ("case_assigned_moderated", "moderated"),
            ("case_assigned_active", "active"),
            ("case_assigned_closed", "closed"),
        ),
        help_text=None,
        initial="case_assigned_moderated",
        field_labels={
            "case_assigned_moderated": _("Moderated"),
            "case_assigned_active": _("Active"),
            "case_assigned_closed": _("Closed"),
        },
    )

    class Meta:
        model = User
        fields = ["is_superuser"]
