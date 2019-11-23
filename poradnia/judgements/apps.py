from django.apps import AppConfig


class JudgementsConfig(AppConfig):
    name = "poradnia.judgements"

    def ready(self):
        from .parsers import nsa  # noqa
        from .parsers import gliwice  # noqa
        from .parsers import warszawa  # noqa
