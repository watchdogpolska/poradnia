from django.core.management import BaseCommand

from poradnia.users.tasks import clear_expired_sessions


class Command(BaseCommand):
    help = "Clear expired sessions from the database"

    def handle(self, **options):
        result = clear_expired_sessions.apply().result
        self.stdout.write(f"deleted={result['deleted']}")
