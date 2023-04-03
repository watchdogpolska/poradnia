import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.utils.translation import gettext as _

from .models import Feedback


class FeedbackFilter(django_filters.FilterSet):
    created = django_filters.DateRangeFilter(label=_("Creation date"))
    status_changed = django_filters.DateRangeFilter(label=_("Status change date"))

    @property
    def form(self):
        self._form = super().form
        self._form.helper = FormHelper(self._form)
        self._form.helper.form_class = "form-inline"
        self._form.helper.form_method = "get"
        self._form.helper.layout.append(Submit("filter", _("Apply Filter")))
        return self._form

    class Meta:
        model = Feedback
        fields = ["user", "status", "status_changed", "created"]
