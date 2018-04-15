from datetime import timedelta

from django.core.management import BaseCommand
from django.utils import timezone

from poradnia.events.models import Reminder, Event


class Command(BaseCommand):
    help = 'Send reminders about upcoming events'
    today = timezone.now()

    def handle(self, **options):
        for event in Event.objects.fresh().prefetch_related('reminder_set').select_related('case').all():
            user_notified = [reminder.user_id for reminder in event.reminder_set.all() if reminder.active]

            for user in event.get_users_with_perms().filter(is_staff=True).select_related('profile').all():
                if user.id in user_notified:
                    self.stdout.write("Skip notification about {} to user {}".format(event,
                                                                                     user))
                    continue
                self.event_for_user(event, user)

    def event_for_user(self, event, user):
        if not hasattr(user, 'profile') or user.profile.event_reminder_time == 0:
            return None

        deadline_days = user.profile.event_reminder_time
        notification_deadline = timedelta(days=deadline_days)

        if self.today + notification_deadline > event.time:
            self.stdout.write("Sending notification about {} to user {}".format(event,
                                                                                user))

            user.notify(actor=user,
                        verb='reminder',
                        target=event,
                        from_email=event.case.get_email())
            Reminder.objects.create(event=event, user=user)
