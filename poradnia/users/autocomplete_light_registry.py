import autocomplete_light
from .models import User
from users.utils import AutocompletePermissionMixin


class UserAutocomplete(AutocompletePermissionMixin, autocomplete_light.AutocompleteModelBase):
    search_fields = ['first_name', 'last_name', 'username']
    model = User
autocomplete_light.register(User, UserAutocomplete)
