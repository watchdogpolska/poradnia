from functools import reduce

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.db.models.expressions import RawSQL
from django.utils.translation import gettext_lazy as _


class ExprAutocompleteMixin:
    def get_search_expr(self):
        if not hasattr(self, "search_expr"):
            raise ImproperlyConfigured(
                "{0} is missing a {0}.search_expr. Define "
                "{0}.search_expr or override {0}.get_search_expr()."
                "".format(self.__class__.__name__)
            )
        return self.search_expr

    def get_filters(self):
        q = [Q(**{x: self.q}) for x in self.get_search_expr()]
        return reduce(lambda x, y: x | y, q)

    def get_queryset(self):
        return self.model.objects.filter(self.get_filters())


class CrispyApplyFilterMixin:
    form_class = "form-inline"

    @property
    def form(self):
        from crispy_forms.helper import FormHelper
        from crispy_forms.layout import Submit

        self._form = super().form
        self._form.helper = FormHelper(self._form)
        if self.form_class:
            self._form.helper.form_class = "form-inline"
        self._form.helper.form_method = "get"
        self._form.helper.layout.append(Submit("filter", _("Apply Filter")))
        return self._form


class FormattedDatetimeMixin:
    def with_formatted_datetime(self, field_name, timezone="UTC"):
        model = self.model
        table_name = model._meta.db_table
        expr = (
            f"CONVERT_TZ({table_name}.{field_name}, @@session.time_zone, '{timezone}')"
        )
        formatted_field_name = f"{field_name}_str"
        formatted_field_expr = RawSQL(
            f"DATE_FORMAT({expr}, '%%Y-%%m-%%d %%H:%%i:%%s')", []
        )
        return self.annotate(**{formatted_field_name: formatted_field_expr})
