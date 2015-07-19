import autocomplete_light
from .models import Case
from users.utils import AutocompletePermissionMixin


class CaseAutocomplete(AutocompletePermissionMixin, autocomplete_light.AutocompleteModelBase):
    search_fields = ['name']
    model = Case

autocomplete_light.register(Case, CaseAutocomplete)
