from datetime import timedelta
import logging

from django.core.management import BaseCommand
from django.db.models import Q
from django.utils import timezone

from poradnia.cases.utils import get_users_with_perm
from poradnia.events.models import Event, Reminder
from poradnia.users.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send reminders about upcoming events"
    today = timezone.now()

    def handle(self, **options):
        for event in (
            Event.objects.fresh()
            .prefetch_related("reminder_set")
            .select_related("case")
            .all()
        ):
            user_notified = [
                reminder.user_id
                for reminder in event.reminder_set.all()
                if reminder.active
            ]
            senders = get_users_with_perm(event.case, "can_send_to_client")
            users = event.get_users_with_perms().filter(is_staff=True).all()

            if senders.count() == 0:
                users = User.objects.filter(
                    Q(pk__in=users) | Q(notify_unassigned_letter=True)
                ).all()
            users = users.select_related("profile")
            for user in users:
                if user.id in user_notified:
                    msg = "Skip notification about {} to user {}".format(event, user)
                    logger.info(msg)
                    continue
                self.event_for_user(event, user)

    def event_for_user(self, event, user):
        if not hasattr(user, "profile"):
            deadline_days = 1
        elif user.profile.event_reminder_time == 0:
            return None
        else:
            deadline_days = user.profile.event_reminder_time

        notification_deadline = timedelta(days=deadline_days)

        if (self.today + notification_deadline > event.time) and (not event.completed):
            msg = "Sending notification about {} to user {}".format(event, user)
            logger.info(msg)

            user.notify(
                actor=user,
                verb="reminder",
                target=event,
                from_email=event.case.get_email(),
            )
            Reminder.objects.create(event=event, user=user)
        elif (self.today + notification_deadline > event.time) and event.completed:
            msg = "Event {} is completed, skipping notification".format(event)
            logger.info(msg)
