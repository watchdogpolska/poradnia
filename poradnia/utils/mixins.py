from functools import reduce

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
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
    

class CrispyApplyFilterMixin(object):
    form_class = 'form-inline'

    @property
    def form(self):
        from crispy_forms.helper import FormHelper
        from crispy_forms.layout import Submit
        self._form = super(CrispyApplyFilterMixin, self).form
        self._form.helper = FormHelper(self._form)
        if self.form_class:
            self._form.helper.form_class = 'form-inline'
        self._form.helper.form_method = 'get'
        self._form.helper.layout.append(Submit('filter', _('Apply Filter')))
        return self._form
