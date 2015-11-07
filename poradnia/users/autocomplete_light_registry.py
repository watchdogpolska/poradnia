import autocomplete_light

from users.utils import AutocompletePermissionMixin

from .models import User


class UserAutocomplete(AutocompletePermissionMixin, autocomplete_light.AutocompleteModelBase):
    search_fields = ['first_name', 'last_name', 'username']
    model = User

    def choice_label(self, choice):
        return "{name} ({email})".format(name=choice.get_nicename(), email=choice.email)
autocomplete_light.register(User, UserAutocomplete)
