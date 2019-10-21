from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from poradnia.judgements.models import Court
from poradnia.judgements.registry import get_parser_keys
from poradnia.judgements.settings import JUDGEMENT_BOT_USERNAME
from poradnia.judgements.utils import Manager


def get_court_ids():
    return (
        Court.objects.filter(active=True)
        .exclude(parser_key="")
        .values_list("id", flat=True)
    )


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("court_ids", nargs="?", choices=get_court_ids())
        parser.add_argument("--parser", choices=get_parser_keys())
        parser.add_argument("--print-all", action="store_true")

    def get_courts(self, court_ids):
        qs = Court.objects
        if court_ids:
            qs = qs.filter(id__in=court_ids)
        return (x for x in qs.all() if x.parser_status)

    def handle(self, *args, **options):
        self.options = options
        self.judgement_bot, _ = get_user_model().objects.get_or_create(
            username=JUDGEMENT_BOT_USERNAME
        )

        manager = Manager(
            bot=self.judgement_bot, stdout=self.stdout, stderr=self.stderr
        )
        for court in self.get_courts(self.options["court_ids"]):
            manager.handle_court(court)
