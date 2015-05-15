import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout
from .models import Advice


class AdviceFilter(django_filters.FilterSet):
    @property
    def form(self):
        self._form = super(AdviceFilter, self).form
        self._form.helper = FormHelper()
        self._form.helper.form_class = 'form-inline'
        self._form.helper.form_method = 'get'
        self._form.helper.layout = Layout(
            'advicer',
            'person_kind',
            'created_by',
            'created_on',
            Submit('save', 'save')
        )
        return self._form

    class Meta:
        model = Advice
        fields = ['advicer', 'created_by', 'created_on', 'person_kind']
