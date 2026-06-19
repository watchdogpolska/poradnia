from django.core.management import BaseCommand

from poradnia.cases.tasks import send_old_cases_reminder


class Command(BaseCommand):
    help = "Send reminders to delete old cases"

    def handle(self, **options):
        result = send_old_cases_reminder.apply().result
        self.stdout.write(
            f"sent={len(result['sent'])} failed={len(result['failed'])}"
        )
