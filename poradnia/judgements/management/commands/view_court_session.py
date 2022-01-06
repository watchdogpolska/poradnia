from django.core.management.base import BaseCommand

from poradnia.judgements.models import Court
from poradnia.judgements.registry import get_parser_keys, parser_registry


def get_court_ids():
    return (
        Court.objects.filter(active=True)
        .exclude(parser_key="")
        .values_list("id", flat=True)
    )


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--parser", choices=get_parser_keys(), required=True)
        parser.add_argument("--signature", required=False)

    def handle(self, *args, **options):
        self.options = options
        signature = options["signature"]
        print(signature)
        parser = parser_registry.get(options["parser"])()
        for session_row in parser.get_session_rows():
            if not signature or session_row.signature != signature:
                continue
            print(session_row)
