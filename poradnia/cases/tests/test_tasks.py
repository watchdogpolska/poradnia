from unittest.mock import patch

from django.core import mail
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from poradnia.cases.factories import CaseFactory
from poradnia.cases.tasks import (
    request_ai_tags_for_case_task,
    search_articles_for_case_task,
    send_old_cases_reminder,
)
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


class SearchArticlesForCaseTaskTestCase(TransactionTestCase):
    def _run(self, case_pk, direct_search=False):
        return search_articles_for_case_task.apply(
            args=[case_pk], kwargs={"direct_search": direct_search}
        ).result

    @patch(
        "poradnia.cases.models.Case.search_articles_for_case",
        return_value=True,
    )
    def test_returns_ok_on_success(self, mock_search):
        case = CaseFactory()
        result = self._run(case.pk)
        self.assertEqual(result, {"case_pk": case.pk, "status": "ok"})
        mock_search.assert_called_once_with(direct_search=False)

    @patch(
        "poradnia.cases.models.Case.search_articles_for_case",
        return_value=False,
    )
    def test_returns_failed_on_failure(self, mock_search):
        case = CaseFactory()
        result = self._run(case.pk)
        self.assertEqual(result, {"case_pk": case.pk, "status": "failed"})

    @patch(
        "poradnia.cases.models.Case.search_articles_for_case",
        return_value=True,
    )
    def test_passes_direct_search_through(self, mock_search):
        case = CaseFactory()
        self._run(case.pk, direct_search=True)
        mock_search.assert_called_once_with(direct_search=True)

    def test_returns_not_found_for_missing_case(self):
        result = self._run(0)
        self.assertEqual(result["case_pk"], 0)
        self.assertEqual(result["status"], "not_found")


class RequestAiTagsForCaseTaskTestCase(TransactionTestCase):
    def _run(self, case_pk):
        return request_ai_tags_for_case_task.apply(args=[case_pk]).result

    @patch(
        "poradnia.cases.models.Case.request_ai_tags_for_case",
        return_value=True,
    )
    def test_returns_ok_on_success(self, mock_request):
        case = CaseFactory()
        result = self._run(case.pk)
        self.assertEqual(result, {"case_pk": case.pk, "status": "ok"})
        mock_request.assert_called_once_with()

    @patch(
        "poradnia.cases.models.Case.request_ai_tags_for_case",
        return_value=False,
    )
    def test_returns_failed_on_failure(self, mock_request):
        case = CaseFactory()
        result = self._run(case.pk)
        self.assertEqual(result, {"case_pk": case.pk, "status": "failed"})

    def test_returns_not_found_for_missing_case(self):
        result = self._run(0)
        self.assertEqual(result["case_pk"], 0)
        self.assertEqual(result["status"], "not_found")
