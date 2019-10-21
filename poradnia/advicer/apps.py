from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class CustomAppConfig(AppConfig):
    name = "poradnia.advicer"
    verbose_name = _("Advicer system")
