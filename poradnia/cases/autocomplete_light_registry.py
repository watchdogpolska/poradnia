import autocomplete_light.shortcuts as autocomplete_light

from users.utils import AutocompletePermissionMixin

from .models import Case


class CaseAutocomplete(AutocompletePermissionMixin, autocomplete_light.AutocompleteModelBase):
    search_fields = ['name']
    model = Case

autocomplete_light.register(Case, CaseAutocomplete)
