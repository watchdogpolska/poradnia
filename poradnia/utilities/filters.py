from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.utils.translation import ugettext_lazy as _


class CrispyFilterMixin(object):
    @property
    def form(self):
        self._form = super(CrispyFilterMixin, self).form
        self._form.helper = FormHelper(self._form)
        self._form.helper.form_class = 'form-inline'
        self._form.helper.form_method = 'get'
        self._form.helper.layout.append(Submit('filter', _('Filter')))
        return self._form
