from datetime import timedelta
from django.core.management import BaseCommand
from django.utils import timezone

from poradnia.events.models import Reminder
from poradnia.users.models import Profile


class Command(BaseCommand):
    help = 'Send reminders about upcoming events'

    def handle(self, **options):
        today = timezone.now()

        # send reminders
        for reminder in Reminder.objects.filter(triggered=False):
            try:
                deadline_days = reminder.user.profile.event_reminder_time
            except Profile.DoesNotExist:
                continue

            notification_deadline = timedelta(days=deadline_days)
            if today + notification_deadline > reminder.event.time:
                self.stdout.write("Sending notification about {} to user {}".format(reminder.event,
                                                                                    reminder.user))
                reminder.user.notify(actor=reminder.user,
                                     verb='alert',
                                     target=reminder.event,
                                     from_email=reminder.event.case.get_email())
                reminder.triggered = True
                reminder.save()

        # clean reminders for past events
        Reminder.objects.filter(triggered=True, event__time__lt=today).delete()
