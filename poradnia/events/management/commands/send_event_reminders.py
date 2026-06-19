from django.core.management import BaseCommand

from poradnia.events.tasks import send_event_reminders


class Command(BaseCommand):
    help = "Send reminders about upcoming events"

    def handle(self, **options):
        result = send_event_reminders.apply().result
        self.stdout.write(
            f"sent={len(result['sent'])} skipped={len(result['skipped'])}"
        )
