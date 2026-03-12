from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CustomAppConfig(AppConfig):
    name = "poradnia.users"
    verbose_name = _("Users")

    def ready(self):
        # Import signal handlers to ensure they are connected
        import poradnia.users.signals  # noqa: F401
