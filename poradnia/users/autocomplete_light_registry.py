import autocomplete_light

from users.utils import AutocompletePermissionMixin

from .models import User


class UserAutocomplete(AutocompletePermissionMixin, autocomplete_light.AutocompleteModelBase):
    search_fields = ['first_name', 'last_name', 'username']
    model = User
autocomplete_light.register(User, UserAutocomplete)
