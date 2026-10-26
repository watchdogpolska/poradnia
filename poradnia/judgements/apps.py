from django.apps import AppConfig


class JudgementsConfig(AppConfig):
    name = "poradnia.judgements"

    def ready(self):
        from .parsers import gliwice, nsa, warszawa  # noqa
