import logging
from datetime import timedelta

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from poradnia.cases.utils import get_users_with_perm
from poradnia.events.models import Event, Reminder
from poradnia.users.models import User

logger = logging.getLogger(__name__)


def _process_event_for_user(event, user, now):
    if not hasattr(user, "profile"):
        deadline_days = 1
    elif user.profile.event_reminder_time == 0:
        return
    else:
        deadline_days = user.profile.event_reminder_time

    notification_deadline = timedelta(days=deadline_days)

    if (now + notification_deadline > event.time) and (not event.completed):
        msg = f"Sending notification about {event} to user {user}"
        logger.info(msg)

        user.notify(
            actor=user,
            verb="reminder",
            target=event,
            from_email=event.case.get_email(),
        )
        Reminder.objects.create(event=event, user=user)

    elif (now + notification_deadline > event.time) and event.completed:
        msg = f"Event {event} is completed, skipping notification"
        logger.info(msg)


@shared_task(
    bind=True,
    ignore_result=False,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_event_reminders(self):
    """
    Send reminders about upcoming events to eligible staff users.
    """
    now = timezone.now()

    events = (
        Event.objects.fresh()
        .prefetch_related("reminder_set")
        .select_related("case")
        .all()
    )

    for event in events:
        user_notified = [
            reminder.user_id for reminder in event.reminder_set.all() if reminder.active
        ]

        senders = get_users_with_perm(event.case, "can_send_to_client")
        users = event.get_users_with_perms().filter(is_staff=True)

        if senders.count() == 0:
            users = User.objects.filter(
                Q(pk__in=users.values_list("pk", flat=True))
                | Q(notify_unassigned_letter=True)
            )

        users = users.select_related("profile")
        skipped = []
        sent = []

        for user in users:
            if user.id in user_notified:
                logger.info(
                    "Skip notification about %s to user %s",
                    event,
                    user,
                )
                skipped.append((user.email, event.id))
                continue

            _process_event_for_user(event, user, now)
            sent.append((user.email, event.id))
        return {"sent": sent, "skipped": skipped}
