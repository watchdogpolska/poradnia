from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CustomAppConfig(AppConfig):
    name = "poradnia.tasty_feedback"
    verbose_name = _("Feedbacks")

    def ready(self):
        import poradnia.tasty_feedback.signals  # noqa: F401
