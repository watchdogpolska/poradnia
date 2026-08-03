from unittest.mock import MagicMock, patch

import requests as requests_lib
from django.contrib.messages import get_messages
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from django.urls import reverse
from guardian.shortcuts import assign_perm
from test_plus.test import TestCase

from poradnia.advicer.factories import AreaFactory, IssueFactory
from poradnia.ai_assistant.models import N8nCaseTagsRequest
from poradnia.cases.factories import CaseFactory
from poradnia.letters.factories import AttachmentFactory, LetterFactory
from poradnia.users.factories import UserFactory

CASE_TAGS_WEBHOOK_SETTINGS = {
    "N8N_CASE_TAGS_WEBHOOK": "https://n8n.example.test/webhook/case-tags",
    "N8N_CASE_TAGS_WEBHOOK_TOKEN": "tags-secret",
    "APP_MODE": "TEST",
}


class CaseRequestAiTagsTestCase(TestCase):
    @override_settings(**CASE_TAGS_WEBHOOK_SETTINGS)
    @patch("poradnia.ai_assistant.models.requests.post")
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
        mock_response.json.return_value = {"request_id": "tag-abc"}
        mock_post.return_value = mock_response

        case.request_ai_tags_for_case()

        _, kwargs = mock_post.call_args
        question = kwargs["json"]["question"]
        self.assertIn("client text", question)
        self.assertIn("attachment text", question)
        self.assertNotIn("staff text", question)

    @override_settings(**CASE_TAGS_WEBHOOK_SETTINGS)
    @patch("poradnia.ai_assistant.models.requests.post")
    def test_saves_n8n_case_tags_request_linked_to_case(self, mock_post):
        case = CaseFactory()
        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "tag-xyz"}
        mock_post.return_value = mock_response

        case.request_ai_tags_for_case()

        obj = N8nCaseTagsRequest.objects.get(request_id="tag-xyz")
        self.assertEqual(obj.case, case)
        self.assertEqual(obj.status, "pending")
        self.assertEqual(obj.environment, "TEST")

    @override_settings(**CASE_TAGS_WEBHOOK_SETTINGS)
    @patch("poradnia.ai_assistant.models.requests.post")
    def test_sends_only_active_tags_in_payload(self, mock_post):
        case = CaseFactory()
        IssueFactory(name="Active Issue")
        IssueFactory(name="Inactive Issue", active=False)
        AreaFactory(name="Active Area")

        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "tag-lists"}
        mock_post.return_value = mock_response

        case.request_ai_tags_for_case()

        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        issue_names = [i["name"] for i in payload["issues_list"]]
        self.assertIn("Active Issue", issue_names)
        self.assertNotIn("Inactive Issue", issue_names)
        area_names = [a["name"] for a in payload["areas_list"]]
        self.assertIn("Active Area", area_names)

    @override_settings(N8N_CASE_TAGS_WEBHOOK="", N8N_CASE_TAGS_WEBHOOK_TOKEN="")
    def test_raises_improperly_configured_when_settings_missing(self):
        case = CaseFactory()
        with self.assertRaises(ImproperlyConfigured):
            case.request_ai_tags_for_case()

    @override_settings(**CASE_TAGS_WEBHOOK_SETTINGS)
    @patch("poradnia.ai_assistant.models.requests.post")
    def test_returns_false_and_saves_error_status_on_http_error(self, mock_post):
        case = CaseFactory()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests_lib.HTTPError("500")
        mock_post.return_value = mock_response

        result = case.request_ai_tags_for_case()

        self.assertFalse(result)
        from poradnia.ai_assistant.models import N8nCaseTagsRequest

        obj = N8nCaseTagsRequest.objects.filter(case=case, status="error").first()
        self.assertIsNotNone(obj)
        self.assertEqual(obj.environment, "TEST")


class CaseRequestAiTagsViewTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory(username="john", password="pass")
        self.case = CaseFactory()
        self.url = reverse("cases:request_ai_tags", kwargs={"pk": self.case.pk})

    def _post(self):
        return self.client.post(self.url)

    def _grant_permission(self):
        assign_perm("cases.can_change_case", self.user, self.case)

    def test_anonymous_user_is_redirected(self):
        response = self._post()
        self.assertEqual(response.status_code, 302)
        self.assertIn("/konta/login/", response["Location"])

    def test_authenticated_user_without_permission_gets_403(self):
        self.client.login(username="john", password="pass")
        response = self._post()
        self.assertEqual(response.status_code, 403)

    def test_get_request_is_not_allowed(self):
        self._grant_permission()
        self.client.login(username="john", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    @patch("poradnia.cases.models.Case.request_ai_tags_for_case")
    def test_permitted_user_triggers_ai_tagging_and_redirects(self, mock_tag):
        self._grant_permission()
        self.client.login(username="john", password="pass")
        response = self._post()
        mock_tag.assert_called_once()
        self.assertRedirects(
            response, self.case.get_absolute_url(), fetch_redirect_response=False
        )

    @patch("poradnia.cases.models.Case.request_ai_tags_for_case", return_value=True)
    def test_success_message_is_set(self, mock_tag):
        self._grant_permission()
        self.client.login(username="john", password="pass")
        response = self._post()
        msgs = list(get_messages(response.wsgi_request))
        self.assertEqual(len(msgs), 1)
        self.assertIn(self.case.name, str(msgs[0]))

    @patch("poradnia.cases.models.Case.request_ai_tags_for_case", return_value=False)
    def test_error_message_is_set_when_tagging_fails(self, mock_tag):
        self._grant_permission()
        self.client.login(username="john", password="pass")
        response = self._post()
        msgs = list(get_messages(response.wsgi_request))
        self.assertEqual(len(msgs), 1)
        self.assertIn(self.case.name, str(msgs[0]))
