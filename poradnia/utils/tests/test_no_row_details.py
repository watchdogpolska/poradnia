from django.test import TestCase
from django.urls import reverse

from poradnia.advicer.factories import AdviceFactory
from poradnia.cases.factories import CaseFactory
from poradnia.events.factories import EventFactory
from poradnia.users.factories import UserFactory


class NoRowDetailsTestCase(TestCase):
    """Datatables without a row tools column must not answer action=details:
    ajax_datatable's default render_row_details() skips .for_user() and
    prints every field unescaped."""

    def _login(self, **kwargs):
        user = UserFactory(**kwargs)
        self.client.login(username=user.username, password="pass")
        return user

    def _details(self, url_name, pk, method="post"):
        send = getattr(self.client, method)
        return send(
            reverse(url_name),
            {"action": "details", "pk": pk},
            headers={"accept": "application/json"},
        )

    def _assert_no_details(self, url_name, pk, secret):
        for method in ("post", "get"):
            resp = self._details(url_name, pk, method=method)
            self.assertEqual(resp.status_code, 404, method)
            self.assertNotContains(resp, secret, status_code=404)

    def test_case_details_not_served(self):
        case = CaseFactory(name="case-secret")
        self._login()
        self._assert_no_details("cases:case_table_ajax_data", case.pk, "case-secret")

    def test_advice_details_not_served(self):
        advice = AdviceFactory(comment="advice-secret")
        self._login()
        self._assert_no_details(
            "advicer:advice_table_ajax_data", advice.pk, "advice-secret"
        )

    def test_event_details_not_served(self):
        event = EventFactory(text="event-secret")
        self._login()
        self._assert_no_details(
            "events:events_table_ajax_data", event.pk, "event-secret"
        )

    def test_user_details_not_served_to_staff(self):
        target = UserFactory(is_staff=True, is_superuser=True)
        self._login(is_staff=True)
        self._assert_no_details(
            "users:users_table_ajax_data", target.pk, target.password
        )

    def test_superuser_gets_no_user_details_either(self):
        target = UserFactory(is_staff=True)
        self._login(is_staff=True, is_superuser=True)
        self._assert_no_details(
            "users:users_table_ajax_data", target.pk, target.password
        )

    def test_anonymous_still_redirected_to_login(self):
        case = CaseFactory()
        resp = self._details("cases:case_table_ajax_data", case.pk)
        self.assertEqual(resp.status_code, 302)

    def test_non_staff_still_redirected_from_users_table(self):
        target = UserFactory()
        self._login()
        resp = self._details("users:users_table_ajax_data", target.pk)
        self.assertEqual(resp.status_code, 302)

    def test_other_actions_still_served(self):
        self._login(is_staff=True, is_superuser=True)
        for url_name in (
            "cases:case_table_ajax_data",
            "advicer:advice_table_ajax_data",
            "events:events_table_ajax_data",
            "users:users_table_ajax_data",
        ):
            resp = self.client.post(
                reverse(url_name),
                {"action": "initialize"},
                headers={"accept": "application/json"},
            )
            self.assertEqual(resp.status_code, 200, url_name)
            self.assertIn("columns", resp.json())
