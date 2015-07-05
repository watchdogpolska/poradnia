import autocomplete_light
from .models import User


class UserAutocomplete(autocomplete_light.AutocompleteModelBase):
    search_fields = ['first_name', 'last_name', 'username']
    model = User

    def choices_for_request(self):
        self.choices = self.choices.for_user(self.request.user)
        return super(UserAutocomplete, self).choices_for_request()
autocomplete_light.register(User, UserAutocomplete)
