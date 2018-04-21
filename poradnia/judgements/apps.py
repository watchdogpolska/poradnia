from django.apps import AppConfig


class JudgementsConfig(AppConfig):
    name = 'poradnia.judgements'

    def ready(self):
        from .parsers import nsa
        from .parsers import gliwice
        from .parsers import warszawa
