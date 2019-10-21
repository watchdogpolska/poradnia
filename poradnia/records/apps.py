from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class CustomAppConfig(AppConfig):
    name = "poradnia.records"
    verbose_name = _("Records")
