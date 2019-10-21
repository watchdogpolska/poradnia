from django.core.management import BaseCommand
from django.db import transaction
from django.utils import translation
from django.utils.module_loading import import_string
from django.utils.timezone import now
from django.utils.translation import ugettext as _
from monotonic import monotonic

from poradnia.stats.models import Item, Value
from poradnia.stats.settings import STAT_METRICS


class Command(BaseCommand):
    help = "Update configured metric stats."

    def add_arguments(self, parser):
        parser.add_argument(
            "comment",
            nargs="?",
            help="Additional comment to call",
            default="Manual call statistics.",
        )

    def handle(self, comment, *args, **options):
        items = {}
        created_count = 0
        from django.conf import settings

        translation.activate(settings.LANGUAGE_CODE)
        for key, import_path in STAT_METRICS.items():
            f = import_string(import_path)
            name = getattr(f, "name", key)
            description = getattr(f, "description", import_path)
            item, created = Item.objects.get_or_create(
                key=key, defaults={"name": name, "description": description}
            )
            if created:
                created_count += 1
            items[key] = item
        self.stdout.write("Registered {} new items.".format(created_count))

        values = []
        start = monotonic()
        time = now()
        for key, import_path in STAT_METRICS.items():
            f = import_string(import_path)
            values.append(Value(item=items[key], time=time, value=f()))
        end = int(monotonic() - start)
        desc = _(
            "Time (seconds) in which metric statistical information was collected."
        )
        system_item, created = Item.objects.get_or_create(
            key="stats.collect_time",
            defaults={"name": _("Time to calculate statistics"), "description": desc},
        )
        values.append(Value(item=system_item, time=time, value=end))

        with transaction.atomic():
            Value.objects.bulk_create(values)
            Item.objects.filter(pk__in=[value.item.pk for value in values]).update(
                last_updated=now()
            )
        self.stdout.write("Registered {} values.".format(len(values)))
        translation.deactivate()
