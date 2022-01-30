from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from poradnia.judgements.models import Court
from poradnia.judgements.registry import get_parser_keys
from poradnia.judgements.settings import JUDGEMENT_BOT_USERNAME
from poradnia.judgements.utils import Manager


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--court", help="Court ID", nargs="+")
        parser.add_argument("--parser", choices=get_parser_keys())

    def get_courts(self, court, parser_key):
        qs = Court.objects
        if court:
            qs = qs.filter(id__in=court)
        if parser_key:
            qs = qs.filter(parser_key=parser_key)

        return (x for x in qs.all() if x.parser_status)

    def handle(self, *args, **options):
        self.options = options
        self.judgement_bot, _ = get_user_model().objects.get_or_create(
            username=JUDGEMENT_BOT_USERNAME
        )

        manager = Manager(
            bot=self.judgement_bot, stdout=self.stdout, stderr=self.stderr
        )
        for court in self.get_courts(self.options["court"], self.options["parser"]):
            manager.handle_court(court)
