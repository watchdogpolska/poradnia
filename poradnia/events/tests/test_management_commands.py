from datetime import timedelta

from django.core import mail, management
from django.test import TestCase
from django.utils import timezone

from cases.factories import CaseFactory
from events.factories import EventFactory
from events.models import Reminder
from users.factories import ProfileFactory, StaffFactory

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class RemindersCommandsTestCase(TestCase):
    def setUp(self):
        self.user = StaffFactory()
        # notify 3 days before event
        ProfileFactory(user=self.user, event_reminder_time=3)
        self.case = CaseFactory(created_by=self.user)

    def test_triggering_reminders(self):
        stdout = StringIO()

        # event in 2 and 4 days from now
        event_should_trigger = EventFactory(case=self.case,
                                            time=timezone.now() + timedelta(days=2))
        event_should_not_trigger = EventFactory(case=self.case,
                                                time=timezone.now() + timedelta(days=4))

        self.assertTrue(self.user.reminder_set.all().count() == 2)

        management.call_command('send_event_reminders', stdout=stdout)

        self.assertTrue(self.user.reminder_set.get(event=event_should_trigger).triggered)
        self.assertFalse(self.user.reminder_set.get(event=event_should_not_trigger).triggered)

    def test_sending_notification(self):
        stdout = StringIO()

        event_to_trigger = EventFactory(case=self.case, time=timezone.now() + timedelta(days=2))
        management.call_command('send_event_reminders', stdout=stdout)
        self.assertTrue(self.user.reminder_set.get(event=event_to_trigger).triggered)

        # check if mail was sent
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox.pop()
        self.assertIn(self.user.email, email.recipients())
        self.assertIn(str(event_to_trigger.case.id), email.subject)
        self.assertIn(event_to_trigger.text, email.body)
        self.assertIn(str(event_to_trigger.case), email.body)

    def test_removing_past_reminders(self):
        stdout = StringIO()

        old_event = EventFactory(case=self.case, time=timezone.now() - timedelta(days=2))
        old_event_reminder = self.user.reminder_set.get(event=old_event)
        old_event_reminder.triggered = True
        old_event_reminder.save()

        triggered_event = EventFactory(case=self.case, time=timezone.now() + timedelta(days=2))
        triggered_event_reminder = self.user.reminder_set.get(event=triggered_event)
        triggered_event_reminder.triggered = True
        triggered_event_reminder.save()

        future_event = EventFactory(case=self.case, time=timezone.now() + timedelta(days=4))
        future_event_reminder = self.user.reminder_set.get(event=future_event)

        management.call_command('send_event_reminders', stdout=stdout)

        with self.assertRaises(Reminder.DoesNotExist):
            # old, triggered reminder should be removed
            old_event_reminder.refresh_from_db()

        triggered_event_reminder.refresh_from_db()
        self.assertTrue(old_event_reminder.triggered)
        future_event_reminder.refresh_from_db()
        self.assertFalse(future_event_reminder.triggered)
