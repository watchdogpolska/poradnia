from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from poradnia.cases.factories import CaseFactory
from poradnia.cases.tasks import send_old_cases_reminder
from poradnia.users.factories import UserFactory

OLD_DATE = timezone.make_aware(timezone.datetime(2000, 1, 1))


class SendOldCasesReminderTaskTestCase(TestCase):
    def _run(self):
        return send_old_cases_reminder.apply().result

    def _make_old_case(self):
        case = CaseFactory()
        case.last_action = OLD_DATE
        case.save(update_fields=["last_action"])
        return case

    def test_no_old_cases_returns_empty_result(self):
        result = self._run()
        self.assertEqual(result["old_cases_count"], 0)
        self.assertEqual(result["sent"], [])
        self.assertEqual(result["failed"], [])

    def test_no_old_cases_sends_no_email(self):
        UserFactory(notify_old_cases=True)
        self._run()
        self.assertEqual(len(mail.outbox), 0)

    def test_sends_email_to_notify_old_cases_users(self):
        self._make_old_case()
        user = UserFactory(notify_old_cases=True)
        self._run()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(user.email, mail.outbox[0].recipients())

    def test_does_not_send_email_to_users_without_flag(self):
        self._make_old_case()
        UserFactory(notify_old_cases=False)
        self._run()
        self.assertEqual(len(mail.outbox), 0)

    def test_sends_to_multiple_users(self):
        self._make_old_case()
        UserFactory(notify_old_cases=True)
        UserFactory(notify_old_cases=True)
        self._run()
        self.assertEqual(len(mail.outbox), 2)

    def test_returns_sent_and_failed(self):
        self._make_old_case()
        user = UserFactory(notify_old_cases=True)
        result = self._run()
        self.assertIn(user.email, result["sent"])
        self.assertEqual(result["failed"], [])

    def test_returns_old_cases_count(self):
        self._make_old_case()
        self._make_old_case()
        UserFactory(notify_old_cases=True)
        result = self._run()
        self.assertEqual(result["old_cases_count"], 2)

    @override_settings(YEARS_TO_STORE_CASES=100)
    def test_recent_case_not_included(self):
        CaseFactory()
        UserFactory(notify_old_cases=True)
        result = self._run()
        self.assertEqual(result["old_cases_count"], 0)
        self.assertEqual(len(mail.outbox), 0)
