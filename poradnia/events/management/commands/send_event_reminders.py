from __future__ import print_function

import datetime

from django.core.management import BaseCommand
from django.utils import timezone

from events.models import Reminder


class Command(BaseCommand):
    help = 'Send reminders about upcoming events'

    def handle(self, **options):
        today = timezone.now()

        # send reminders
        for reminder in Reminder.objects.filter(triggered=False):
            notification_deadline = datetime.timedelta(days=reminder.user.profile.event_reminder_time)
            if today + notification_deadline > reminder.event.time:
                print("Sending notification about {} to user {}".format(reminder.event, reminder.user))
                reminder.triggered = True
                reminder.save()

        # clean reminders for past events
        Reminder.objects.filter(triggered=True, event__time__lt=today).delete()
