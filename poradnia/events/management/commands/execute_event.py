from __future__ import absolute_import

from django.core.management.base import BaseCommand

from ...models import Event


class Command(BaseCommand):
    help = 'Execute all events and create accordingly alarms'

    def handle(self, **options):
        for alarm in Event.objects.untriggered().old().all():
            self.stdout.write(alarm.execute())
