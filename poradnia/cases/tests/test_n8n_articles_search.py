from unittest.mock import MagicMock, patch

import requests as requests_lib
from django.contrib.messages import get_messages
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from django.urls import reverse
from guardian.shortcuts import assign_perm
from test_plus.test import TestCase

from ai_assistant.models import N8nArticlesSearchRequest
from poradnia.cases.factories import CaseFactory
from poradnia.letters.factories import AttachmentFactory, LetterFactory
from poradnia.users.factories import UserFactory

ARTICLES_SEARCH_WEBHOOK_SETTINGS = {
    "N8N_ARTICLES_SEARCH_WEBHOOK": "https://n8n.example.test/webhook/articles-search",
    "N8N_ARTICLES_SEARCH_WEBHOOK_TOKEN": "search-secret",
    "APP_MODE": "TEST",
}


class ArticlesSearchRequestTestCase(TestCase):
    @override_settings(**ARTICLES_SEARCH_WEBHOOK_SETTINGS)
    @patch("ai_assistant.models.requests.post")
    def test_client_letters_and_attachments_form_question(self, mock_post):
        client = UserFactory(is_staff=False)
        advisor = UserFactory(is_staff=True)
        case = CaseFactory(client=client)

        client_letter = LetterFactory(
            case=case, created_by=client, created_by_is_staff=False, text="client text"
        )
        AttachmentFactory(letter=client_letter, text_content="attachment text")
        LetterFactory(
            case=case, created_by=advisor, created_by_is_staff=True, text="staff text"
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "search-abc"}
        mock_post.return_value = mock_response

        case.search_articles_for_case()

        _, kwargs = mock_post.call_args
        question = kwargs["json"]["chatInput"]
        self.assertIn("client text", question)
        self.assertIn("attachment text", question)
        self.assertNotIn("staff text", question)

    @override_settings(**ARTICLES_SEARCH_WEBHOOK_SETTINGS)
    @patch("ai_assistant.models.requests.post")
    def test_saves_n8n_articles_search_request_linked_to_case(self, mock_post):
        case = CaseFactory()
        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "search-xyz"}
        mock_post.return_value = mock_response

        case.search_articles_for_case()

        obj = N8nArticlesSearchRequest.objects.get(request_id="search-xyz")
        self.assertEqual(obj.case, case)
        self.assertEqual(obj.status, "pending")
        self.assertEqual(obj.environment, "TEST")

    @override_settings(
        N8N_ARTICLES_SEARCH_WEBHOOK="", N8N_ARTICLES_SEARCH_WEBHOOK_TOKEN=""
    )
    def test_raises_improperly_configured_when_settings_missing(self):
        case = CaseFactory()
        with self.assertRaises(ImproperlyConfigured):
            case.search_articles_for_case()

    @override_settings(**ARTICLES_SEARCH_WEBHOOK_SETTINGS)
    @patch("ai_assistant.models.requests.post")
    def test_returns_false_and_saves_error_status_on_http_error(self, mock_post):
        case = CaseFactory()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests_lib.HTTPError("500")
        mock_post.return_value = mock_response

        result = case.search_articles_for_case()

        self.assertFalse(result)
        obj = N8nArticlesSearchRequest.objects.filter(case=case, status="error").first()
        self.assertIsNotNone(obj)
        self.assertEqual(obj.environment, "TEST")

    @override_settings(**ARTICLES_SEARCH_WEBHOOK_SETTINGS)
    @patch("ai_assistant.models.requests.post")
    def test_returns_true_on_success(self, mock_post):
        case = CaseFactory()
        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "search-ok"}
        mock_post.return_value = mock_response

        result = case.search_articles_for_case()

        self.assertTrue(result)


class CaseSearchArticlesViewTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory(username="john", password="pass")
        self.case = CaseFactory()
        self.search_url = reverse("cases:search_articles", kwargs={"pk": self.case.pk})
        self.classify_url = reverse(
            "cases:classify_and_search_articles", kwargs={"pk": self.case.pk}
        )

    def _grant_permission(self):
        assign_perm("cases.can_change_case", self.user, self.case)

    def test_anonymous_user_is_redirected(self):
        response = self.client.post(self.search_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/konta/login/", response["Location"])

    def test_authenticated_user_without_permission_gets_403(self):
        self.client.login(username="john", password="pass")
        response = self.client.post(self.search_url)
        self.assertEqual(response.status_code, 403)

    def test_get_request_is_not_allowed(self):
        self._grant_permission()
        self.client.login(username="john", password="pass")
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 405)

    @patch(
        "poradnia.cases.models.Case.search_articles_for_case", return_value=True
    )
    def test_direct_search_success_message(self, mock_search):
        self._grant_permission()
        self.client.login(username="john", password="pass")
        response = self.client.post(self.search_url)
        msgs = list(get_messages(response.wsgi_request))
        self.assertEqual(len(msgs), 1)
        self.assertIn(self.case.name, str(msgs[0]))
        self.assertRedirects(
            response, self.case.get_absolute_url(), fetch_redirect_response=False
        )

    @patch(
        "poradnia.cases.models.Case.search_articles_for_case", return_value=True
    )
    def test_classify_and_search_success_message(self, mock_search):
        self._grant_permission()
        self.client.login(username="john", password="pass")
        response = self.client.post(self.classify_url)
        msgs = list(get_messages(response.wsgi_request))
        self.assertEqual(len(msgs), 1)
        self.assertIn(self.case.name, str(msgs[0]))

    @patch(
        "poradnia.cases.models.Case.search_articles_for_case", return_value=False
    )
    def test_error_message_is_set_when_search_fails(self, mock_search):
        self._grant_permission()
        self.client.login(username="john", password="pass")
        response = self.client.post(self.search_url)
        msgs = list(get_messages(response.wsgi_request))
        self.assertEqual(len(msgs), 1)
        self.assertIn(self.case.name, str(msgs[0]))
