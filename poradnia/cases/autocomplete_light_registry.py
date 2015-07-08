import autocomplete_light
from .models import Case


class CaseAutocomplete(autocomplete_light.AutocompleteModelBase):
    search_fields = ['name']
    model = Case

    def choices_for_request(self):
        self.choices = self.choices.for_user(self.request.user)
        return super(CaseAutocomplete, self).choices_for_request()
autocomplete_light.register(Case, CaseAutocomplete)
