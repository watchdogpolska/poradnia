from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout
import autocomplete_light
from .models import Advice


class AdviceFilter(django_filters.FilterSet):
    advicer = django_filters.ModelChoiceFilter(
        queryset=get_user_model().objects.all(),
        widget=autocomplete_light.ChoiceWidget('UserAutocomplete'),
        label=_("Advicer"),
        )
    created_by = django_filters.ModelChoiceFilter(
        queryset=get_user_model().objects.all(),
        widget=autocomplete_light.ChoiceWidget('UserAutocomplete'),
        label=_("Created by"),
        )
    created_on = django_filters.DateRangeFilter(label=_("Created on"))

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
