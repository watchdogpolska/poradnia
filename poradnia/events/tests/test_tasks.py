from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from poradnia.cases.factories import CaseFactory, CaseUserObjectPermissionFactory
from poradnia.events.factories import EventFactory
from poradnia.events.tasks import send_event_reminders
from poradnia.users.factories import ProfileFactory, StaffFactory, UserFactory


class SendEventRemindersTaskTestCase(TestCase):
    def setUp(self):
        self.user = StaffFactory()
        ProfileFactory(user=self.user, event_reminder_time=3)
        self.case = CaseFactory(created_by=self.user)

    def _run(self):
        return send_event_reminders.apply().result

    def test_processes_all_events(self):
        # regression: return was inside the for-event loop, only first event was processed
        EventFactory(case=self.case, time=timezone.now() + timedelta(days=2))
        EventFactory(case=self.case, time=timezone.now() + timedelta(days=2))
        self._run()
        self.assertEqual(len(mail.outbox), 2)

    def test_triggering_reminders(self):
        event_should_trigger = EventFactory(
            case=self.case, time=timezone.now() + timedelta(days=2)
        )
        event_should_not_trigger = EventFactory(
            case=self.case, time=timezone.now() + timedelta(days=4)
        )
        self._run()
        self.assertTrue(
            self.user.reminder_set.filter(event=event_should_trigger).exists()
        )
        self.assertFalse(
            self.user.reminder_set.filter(event=event_should_not_trigger).exists()
        )

    def test_sends_notification_email(self):
        event = EventFactory(case=self.case, time=timezone.now() + timedelta(days=2))
        self._run()
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn(self.user.email, email.recipients())
        self.assertIn(str(event.case.id), email.subject)
        self.assertIn(event.text, email.body)

    def test_sends_notification_if_no_profile(self):
        cuop = CaseUserObjectPermissionFactory(
            user__profile=False, user__is_staff=True, content_object=self.case
        )
        EventFactory(case=self.case, time=timezone.now())
        self._run()
        self.assertTrue(cuop.user.reminder_set.filter().exists())
        all_recipients = [r for email in mail.outbox for r in email.recipients()]
        self.assertIn(cuop.user.email, all_recipients)

    def test_send_notification_once_to_user(self):
        EventFactory(case=self.case, time=timezone.now() + timedelta(days=2))
        self._run()
        self._run()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.user.reminder_set.count(), 1)

    def test_send_notification_to_management_in_free_cases(self):
        free_case = CaseFactory()
        management_user = UserFactory(notify_unassigned_letter=True)
        EventFactory(case=free_case, time=timezone.now())
        self._run()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(management_user.email, mail.outbox[0].recipients())

    def test_returns_sent_skipped_counts(self):
        EventFactory(case=self.case, time=timezone.now() + timedelta(days=2))
        result = self._run()
        self.assertIn("sent", result)
        self.assertIn("skipped", result)
        self.assertEqual(len(result["sent"]), 1)
        self.assertEqual(len(result["skipped"]), 0)
