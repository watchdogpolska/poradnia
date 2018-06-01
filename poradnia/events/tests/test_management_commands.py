from datetime import timedelta

from django.core import mail, management
from django.test import TestCase
from django.utils import timezone

from poradnia.cases.factories import CaseFactory, CaseUserObjectPermissionFactory
from poradnia.events.factories import EventFactory
from poradnia.users.factories import ProfileFactory, StaffFactory, UserFactory

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
        self.stdout = StringIO()

    def test_triggering_reminders(self):
        # event in 2 and 4 days from now
        event_should_trigger = EventFactory(case=self.case,
                                            time=timezone.now() + timedelta(days=2))
        event_should_not_trigger = EventFactory(case=self.case,
                                                time=timezone.now() + timedelta(days=4))

        management.call_command('send_event_reminders', stdout=self.stdout)

        self.assertTrue(self.user.reminder_set.filter(event=event_should_trigger).exists())
        self.assertFalse(self.user.reminder_set.filter(event=event_should_not_trigger).exists())

    def test_sending_notification(self):
        event_to_trigger = EventFactory(case=self.case, time=timezone.now() + timedelta(days=2))
        management.call_command('send_event_reminders', stdout=self.stdout)
        self.assertTrue(self.user.reminder_set.filter(event=event_to_trigger).exists())

        # check if mail was sent
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox.pop()
        self.assertIn(self.user.email, email.recipients())
        self.assertIn(str(event_to_trigger.case.id), email.subject)
        self.assertIn(event_to_trigger.text, email.body)
        self.assertIn(str(event_to_trigger.case), email.body)

    def test_sending_notification_if_no_profile(self):
        cuop = CaseUserObjectPermissionFactory(user__profile=None,
                                               user__is_staff=True,
                                               content_object=self.case)
        event_to_trigger = EventFactory(case=self.case, time=timezone.now())
        management.call_command('send_event_reminders', stdout=self.stdout)

        self.assertTrue(cuop.user.reminder_set.filter(event=event_to_trigger).exists())

        email = mail.outbox.pop()
        self.assertIn(cuop.user.email, email.recipients())

    def test_send_notification_once_to_user(self):
        EventFactory(case=self.case, time=timezone.now() + timedelta(days=2))
        management.call_command('send_event_reminders', stdout=self.stdout)
        management.call_command('send_event_reminders', stdout=self.stdout)

        # check if email was sent once
        self.assertEqual(len(mail.outbox), 1)

        # check if reminder was saved once
        self.assertTrue(self.user.reminder_set.count(), 1)

    def test_send_notification_to_management_in_free_cases(self):
        free_case = CaseFactory()
        management_user = UserFactory(notify_unassigned_letter=True)

        EventFactory(case=free_case,
                     time=timezone.now())

        management.call_command('send_event_reminders', stdout=self.stdout)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox.pop()
        self.assertIn(management_user.email, email.recipients())
