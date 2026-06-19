from io import StringIO

from django.core import mail, management
from django.test import TestCase
from django.utils import timezone

from poradnia.cases.factories import CaseFactory
from poradnia.users.factories import UserFactory

OLD_DATE = timezone.make_aware(timezone.datetime(2000, 1, 1))


class SendOldCasesReminderCommandTestCase(TestCase):
    def _run(self):
        stdout = StringIO()
        management.call_command("send_old_cases_reminder", stdout=stdout)
        return stdout.getvalue()

    def _make_old_case(self):
        case = CaseFactory()
        case.last_action = OLD_DATE
        case.save(update_fields=["last_action"])
        return case

    def test_sends_email_when_old_cases_exist(self):
        self._make_old_case()
        UserFactory(notify_old_cases=True)
        self._run()
        self.assertEqual(len(mail.outbox), 1)

    def test_no_email_when_no_old_cases(self):
        UserFactory(notify_old_cases=True)
        self._run()
        self.assertEqual(len(mail.outbox), 0)

    def test_outputs_sent_and_failed_counts(self):
        self._make_old_case()
        UserFactory(notify_old_cases=True)
        output = self._run()
        self.assertIn("sent=1", output)
        self.assertIn("failed=0", output)

    def test_outputs_zero_counts_when_no_old_cases(self):
        output = self._run()
        self.assertIn("sent=0", output)
        self.assertIn("failed=0", output)
