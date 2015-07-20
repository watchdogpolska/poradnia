from django.contrib.auth import get_user_model
from django_filters import ModelChoiceFilter
import autocomplete_light


class UserChoiceFilter(ModelChoiceFilter):
    def __init__(self, queryset=get_user_model().objects.all(),
            widget=autocomplete_light.ChoiceWidget('UserAutocomplete'), *args, **kwargs):
        super(UserChoiceFilter, self).__init__(queryset=queryset, widget=widget, *args, **kwargs)
