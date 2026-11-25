from unittest.mock import MagicMock, patch

import requests as requests_lib
from django.contrib.messages import get_messages
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from django.urls import reverse
from guardian.shortcuts import assign_perm
from test_plus.test import TestCase

from poradnia.advicer.factories import (
    AdviceFactory,
    InstitutionKindFactory,
    ScopeFactory,
)
from poradnia.ai_assistant.models import N8nSimilarCasesRequest
from poradnia.cases.factories import CaseFactory
from poradnia.letters.factories import LetterFactory
from poradnia.users.factories import StaffFactory, UserFactory

SIMILAR_CASES_WEBHOOK_SETTINGS = {
    "N8N_SIMILAR_CASES_WEBHOOK": "https://n8n.example.test/webhook/similar-cases",
    "N8N_SIMILAR_CASES_WEBHOOK_TOKEN": "similar-secret",
    "APP_MODE": "TEST",
}
HTTP_POST = "poradnia.ai_assistant.models.requests.post"


def accepted_response(request_id="sim-abc"):
    response = MagicMock()
    response.json.return_value = {"request_id": request_id, "status": "accepted"}
    return response


@override_settings(**SIMILAR_CASES_WEBHOOK_SETTINGS)
class FindSimilarCasesTestCase(TestCase):
    def setUp(self):
        self.staff = StaffFactory()
        self.client_user = UserFactory(is_staff=False)
        self.case = CaseFactory(client=self.client_user)
        LetterFactory(
            case=self.case,
            created_by=self.client_user,
            created_by_is_staff=False,
            text="client text",
        )
        LetterFactory(
            case=self.case,
            created_by=self.staff,
            created_by_is_staff=True,
            text="staff text",
        )
        self.kind = InstitutionKindFactory(name="Gmina")
        self.scope = ScopeFactory(is_dip=True, is_local_government=True, is_slapp=False)

    def _advice(self, **kwargs):
        return AdviceFactory(case=self.case, **kwargs)

    @patch(HTTP_POST, return_value=accepted_response())
    def test_kind_and_scope_from_advice(self, mock_post):
        self._advice(institution_kind=self.kind, scope=self.scope)

        result = self.case.find_similar_cases(requested_by=self.staff)

        self.assertEqual(result, (True, "started"))
        args, kwargs = mock_post.call_args
        self.assertEqual(
            args[0], SIMILAR_CASES_WEBHOOK_SETTINGS["N8N_SIMILAR_CASES_WEBHOOK"]
        )
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer similar-secret")
        self.assertEqual(kwargs["timeout"], 10)
        self.assertEqual(
            kwargs["json"],
            {
                "environment": "TEST",
                "case_id": self.case.pk,
                "client_id": self.client_user.pk,
                "question": "client text",
                "institution_kind_id": self.kind.pk,
                "institution_kind_name": "Gmina",
                "scope_id": self.scope.pk,
                "scope_flags": {
                    "is_dip": True,
                    "is_local_government": True,
                    "is_slapp": False,
                },
            },
        )
        obj = N8nSimilarCasesRequest.objects.get(request_id="sim-abc")
        self.assertEqual(obj.case, self.case)
        self.assertEqual(obj.requested_by, self.staff)
        self.assertEqual(obj.status, "pending")
        self.assertEqual(obj.environment, "TEST")
        self.assertEqual(obj.question, "client text")
        self.assertEqual(
            (obj.institution_kind, obj.institution_kind_source), (self.kind, "advice")
        )
        self.assertEqual((obj.scope, obj.scope_source), (self.scope, "advice"))

    @patch(HTTP_POST, return_value=accepted_response())
    def test_kind_and_scope_from_ai_tags(self, mock_post):
        self._advice(
            ai_assistant_tags={"institution_kind": self.kind.pk, "scope": self.scope.pk}
        )

        self.assertEqual(self.case.find_similar_cases(self.staff), (True, "started"))

        obj = N8nSimilarCasesRequest.objects.get()
        self.assertEqual(
            (obj.institution_kind, obj.institution_kind_source), (self.kind, "ai_tags")
        )
        self.assertEqual((obj.scope, obj.scope_source), (self.scope, "ai_tags"))
        self.assertEqual(mock_post.call_args.kwargs["json"]["scope_id"], self.scope.pk)

    @patch(HTTP_POST, return_value=accepted_response())
    def test_advice_tags_win_over_ai_tags(self, mock_post):
        self._advice(
            institution_kind=self.kind,
            scope=self.scope,
            ai_assistant_tags={
                "institution_kind": InstitutionKindFactory().pk,
                "scope": ScopeFactory().pk,
            },
        )
        self.case.find_similar_cases(self.staff)
        obj = N8nSimilarCasesRequest.objects.get()
        self.assertEqual((obj.institution_kind, obj.scope), (self.kind, self.scope))

    @patch(HTTP_POST)
    def test_pre_check_failures_create_no_request(self, mock_post):
        undefined = InstitutionKindFactory(is_undefined=True)
        out_of_scope = ScopeFactory(is_out_of_scope=True)
        variants = {
            "no advice": (None, "no_institution_kind"),
            "no kind": ({"scope": self.scope}, "no_institution_kind"),
            "undefined kind": (
                {"institution_kind": undefined, "scope": self.scope},
                "no_institution_kind",
            ),
            "ai kind does not exist": (
                {"ai_assistant_tags": {"institution_kind": 999999}},
                "no_institution_kind",
            ),
            "undefined ai kind": (
                {"ai_assistant_tags": {"institution_kind": undefined.pk}},
                "no_institution_kind",
            ),
            "no scope": ({"institution_kind": self.kind}, "no_scope"),
            "ai scope does not exist": (
                {"institution_kind": self.kind, "ai_assistant_tags": {"scope": 999999}},
                "no_scope",
            ),
            "out of scope": (
                {"institution_kind": self.kind, "scope": out_of_scope},
                "out_of_scope",
            ),
            "out of scope from ai tags": (
                {
                    "institution_kind": self.kind,
                    "ai_assistant_tags": {"scope": out_of_scope.pk},
                },
                "out_of_scope",
            ),
        }
        for label, (advice_kwargs, code) in variants.items():
            with self.subTest(label):
                case = CaseFactory()
                LetterFactory(case=case, created_by=case.client, text="client text")
                if advice_kwargs is not None:
                    AdviceFactory(case=case, **advice_kwargs)
                self.assertEqual(case.find_similar_cases(self.staff), (False, code))
        self.assertFalse(N8nSimilarCasesRequest.objects.exists())
        mock_post.assert_not_called()

    @patch(HTTP_POST)
    def test_no_client_text(self, mock_post):
        case = CaseFactory()
        LetterFactory(case=case, created_by=self.staff, created_by_is_staff=True)
        AdviceFactory(case=case, institution_kind=self.kind, scope=self.scope)

        self.assertEqual(case.find_similar_cases(self.staff), (False, "no_client_text"))
        self.assertFalse(N8nSimilarCasesRequest.objects.exists())
        mock_post.assert_not_called()

    @patch(HTTP_POST)
    def test_transport_error(self, mock_post):
        self._advice(institution_kind=self.kind, scope=self.scope)
        mock_post.side_effect = requests_lib.ConnectionError("down")

        self.assertEqual(
            self.case.find_similar_cases(self.staff), (False, "request_failed")
        )
        obj = N8nSimilarCasesRequest.objects.get()
        self.assertEqual(obj.status, "error")
        self.assertTrue(obj.request_id)

    @override_settings(N8N_SIMILAR_CASES_WEBHOOK="", N8N_SIMILAR_CASES_WEBHOOK_TOKEN="")
    def test_raises_improperly_configured_when_settings_missing(self):
        self._advice(institution_kind=self.kind, scope=self.scope)
        with self.assertRaises(ImproperlyConfigured):
            self.case.find_similar_cases(self.staff)


class CaseFindSimilarCasesViewTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory(username="john", password="pass")
        self.case = CaseFactory()
        self.url = reverse("cases:find_similar_cases", kwargs={"pk": self.case.pk})

    def _grant_permission(self):
        assign_perm("cases.can_change_case", self.user, self.case)

    def test_url(self):
        self.assertEqual(self.url, f"/sprawy/sprawa-{self.case.pk}/podobne-sprawy/")

    def test_anonymous_user_is_redirected(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/konta/login/", response["Location"])

    def test_authenticated_user_without_permission_gets_403(self):
        self.client.login(username="john", password="pass")
        self.assertEqual(self.client.post(self.url).status_code, 403)

    def test_get_request_is_not_allowed(self):
        self._grant_permission()
        self.client.login(username="john", password="pass")
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_messages(self):
        self._grant_permission()
        self.client.login(username="john", password="pass")
        expected = {
            (False, "no_institution_kind"): (
                "warning",
                "Najpierw otaguj sprawę – brak rodzaju instytucji.",
            ),
            (False, "no_scope"): ("warning", "Najpierw otaguj sprawę – brak zakresu."),
            (False, "out_of_scope"): (
                "warning",
                "Sprawa poza zakresem poradnictwa – nie ma podobnych spraw do "
                "porównania.",
            ),
            (False, "no_client_text"): (
                "warning",
                "Brak wiadomości od klienta – nie ma czego porównać.",
            ),
            (True, "started"): (
                "success",
                "Wyszukiwanie podobnych zamkniętych spraw rozpoczęte dla "
                f"„{self.case.name}”.",
            ),
            (False, "request_failed"): (
                "error",
                f'Prośba o wyszukiwanie podobnych zamkniętych spraw dla "{self.case.name}"'
                " zakończyła się niepowodzeniem. Proszę, spróbuj ponownie później.",
            ),
        }
        for result, (level, text) in expected.items():
            with (
                self.subTest(result),
                patch(
                    "poradnia.cases.models.Case.find_similar_cases", return_value=result
                ) as mock_find,
            ):
                response = self.client.post(self.url)
                # The redirect isn't followed, so read (and thereby consume)
                # the stored messages; the newest one is this request's.
                msgs = list(get_messages(response.wsgi_request))
                self.assertEqual((msgs[-1].level_tag, str(msgs[-1])), (level, text))
                self.assertRedirects(
                    response,
                    self.case.get_absolute_url(),
                    fetch_redirect_response=False,
                )
                self.assertEqual(mock_find.call_args.kwargs["requested_by"], self.user)


class CaseDetailSimilarCasesMenuTestCase(TestCase):
    def setUp(self):
        self.user = StaffFactory(is_superuser=True)
        self.client.force_login(self.user)
        self.case = CaseFactory()
        self.find_url = reverse("cases:find_similar_cases", kwargs={"pk": self.case.pk})

    @override_settings(N8N_SIMILAR_CASES_WEBHOOK="")
    def test_menu_entry_hidden_without_webhook(self):
        response = self.client.get(self.case.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, reverse("cases:search_articles", kwargs={"pk": self.case.pk})
        )
        self.assertNotContains(response, self.find_url)

    @override_settings(**SIMILAR_CASES_WEBHOOK_SETTINGS)
    def test_menu_entry_shown_with_webhook(self):
        response = self.client.get(self.case.get_absolute_url())
        self.assertContains(response, self.find_url)
        self.assertContains(response, "Znajdź podobne zamknięte sprawy")
