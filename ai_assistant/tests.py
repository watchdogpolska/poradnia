import json
from unittest.mock import MagicMock, patch

import requests as req_lib
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from ai_assistant import views as views_module
from ai_assistant.models import N8nArticlesSearchRequest
from poradnia.cases.factories import CaseFactory
from poradnia.letters.models import Letter

WEBHOOK_URL = "http://n8n.example.com/webhook/articles"
WEBHOOK_SETTINGS = {
    "N8N_ARTICLES_SEARCH_WEBHOOK": WEBHOOK_URL,
    "N8N_ARTICLES_SEARCH_WEBHOOK_TOKEN": "webhook-secret",
    "APP_MODE": "TEST",
}
CALLBACK_SETTINGS = {"N8N_ARTICLES_SEARCH_CALLBACK_TOKEN": "callback-secret"}


def _json(response):
    return json.loads(response.content.decode("utf-8"))


SAMPLE_RESPONSE = """\
Uzyteczne artykuly w sprawie:

- https://example.com/article-1

**Temat:** Tytuł pierwszego artykułu

**Podsumowanie:** Pierwsze podsumowanie.

- https://example.com/article-2

**Temat:** Tytuł drugiego artykułu

**Podsumowanie:** Drugie podsumowanie.
"""

SAMPLE_RESPONSE_MD_LINKS = """\
Uzyteczne artykuly w sprawie:

- [https://example.com/article-1](https://example.com/article-1)

**Temat:** Tytuł pierwszego artykułu

**Podsumowanie:** Pierwsze podsumowanie.
"""


class FormatArticlesHtmlTestCase(SimpleTestCase):
    def _fmt(self, text):
        return views_module._format_articles_html(text)

    def test_empty_string_returns_empty(self):
        self.assertEqual(self._fmt(""), "")

    def test_whitespace_only_returns_empty(self):
        self.assertEqual(self._fmt("   \n  "), "")

    def test_title_only_no_articles(self):
        html = self._fmt("Tylko tytuł")
        self.assertIn("<strong>ASYSTENT AI - Tylko tytuł</strong>", html)
        self.assertNotIn("<ul>", html)

    def test_full_sample_contains_title(self):
        html = self._fmt(SAMPLE_RESPONSE)
        self.assertIn(
            "<strong>ASYSTENT AI - Uzyteczne artykuly w sprawie:</strong>", html
        )

    def test_full_sample_contains_links(self):
        html = self._fmt(SAMPLE_RESPONSE)
        self.assertIn('href="https://example.com/article-1"', html)
        self.assertIn('href="https://example.com/article-2"', html)

    def test_links_open_in_new_tab(self):
        html = self._fmt(SAMPLE_RESPONSE)
        self.assertIn('target="_blank"', html)
        self.assertIn('rel="noopener noreferrer"', html)

    def test_full_sample_contains_subjects(self):
        html = self._fmt(SAMPLE_RESPONSE)
        self.assertIn("Tytuł pierwszego artykułu", html)
        self.assertIn("Tytuł drugiego artykułu", html)

    def test_full_sample_contains_summaries(self):
        html = self._fmt(SAMPLE_RESPONSE)
        self.assertIn("Pierwsze podsumowanie.", html)
        self.assertIn("Drugie podsumowanie.", html)

    def test_full_sample_wraps_articles_in_ul(self):
        html = self._fmt(SAMPLE_RESPONSE)
        self.assertIn("<ul>", html)
        self.assertIn("</ul>", html)

    def test_markdown_link_format_also_works(self):
        html = self._fmt(SAMPLE_RESPONSE_MD_LINKS)
        self.assertIn('href="https://example.com/article-1"', html)
        self.assertIn("Tytuł pierwszego artykułu", html)

    def test_html_escapes_dangerous_content(self):
        malicious = (
            "Title\n"
            "- https://example.com/\n"
            "**Temat:** <script>alert(1)</script>\n"
            "**Podsumowanie:** <b>bold</b>\n"
        )
        html = self._fmt(malicious)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)


class N8nArticlesSearchHelpersTestCase(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, body=b"{}", token=None, content_type="application/json"):
        request = self.factory.post("/", data=body, content_type=content_type)
        if token is not None:
            request.headers = {"Authorization": f"Bearer {token}"}
        else:
            request.headers = {}
        return request

    @override_settings(N8N_ARTICLES_SEARCH_CALLBACK_TOKEN="")
    def test_check_token_not_configured_returns_503(self):
        response = views_module._check_token(self._request(token="any"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(_json(response)["error"]["code"], "webhook_not_configured")

    @override_settings(N8N_ARTICLES_SEARCH_CALLBACK_TOKEN="secret")
    def test_check_token_missing_bearer_returns_401(self):
        response = views_module._check_token(self._request(token=None))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(_json(response)["error"]["message"], "Missing bearer token.")

    @override_settings(N8N_ARTICLES_SEARCH_CALLBACK_TOKEN="secret")
    def test_check_token_invalid_returns_401(self):
        response = views_module._check_token(self._request(token="wrong"))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(_json(response)["error"]["message"], "Invalid bearer token.")

    @override_settings(N8N_ARTICLES_SEARCH_CALLBACK_TOKEN="secret")
    def test_check_token_valid_returns_none(self):
        result = views_module._check_token(self._request(token="secret"))
        self.assertIsNone(result)

    def test_parse_payload_invalid_utf8(self):
        payload, err = views_module._parse_payload(self._request(body=b"\xff"))

        self.assertIsNone(payload)
        self.assertEqual(err.status_code, 400)
        self.assertEqual(_json(err)["error"]["code"], "invalid_json")

    def test_parse_payload_invalid_json(self):
        payload, err = views_module._parse_payload(self._request(body=b"{bad}"))

        self.assertIsNone(payload)
        self.assertEqual(err.status_code, 400)
        self.assertEqual(_json(err)["error"]["code"], "invalid_json")

    def test_parse_payload_non_object(self):
        body = json.dumps([1, 2, 3]).encode()
        payload, err = views_module._parse_payload(self._request(body=body))

        self.assertIsNone(payload)
        self.assertEqual(err.status_code, 400)
        self.assertEqual(_json(err)["error"]["code"], "invalid_payload")

    def test_parse_payload_ok(self):
        body = json.dumps({"key": "value"}).encode()
        payload, err = views_module._parse_payload(self._request(body=body))

        self.assertEqual(payload, {"key": "value"})
        self.assertIsNone(err)


class N8nArticlesSearchRequestModelTestCase(TestCase):
    @override_settings(
        N8N_ARTICLES_SEARCH_WEBHOOK="",
        N8N_ARTICLES_SEARCH_WEBHOOK_TOKEN="",
        APP_MODE="TEST",
    )
    def test_search_articles_raises_when_unconfigured(self):
        obj = N8nArticlesSearchRequest(question="test")

        with self.assertRaises(ImproperlyConfigured):
            obj.search_articles()

    @override_settings(**WEBHOOK_SETTINGS)
    @patch("ai_assistant.models.requests.post")
    def test_search_articles_sends_correct_payload(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "abc-123"}
        mock_post.return_value = mock_response

        obj = N8nArticlesSearchRequest(question="Is this FOI?", direct_search=False)
        obj.search_articles()

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], WEBHOOK_URL)
        self.assertEqual(kwargs["json"]["chatInput"], "Is this FOI?")
        self.assertEqual(kwargs["json"]["environment"], "TEST")
        self.assertFalse(kwargs["json"]["direct_search"])
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer webhook-secret")

    @override_settings(**WEBHOOK_SETTINGS)
    @patch("ai_assistant.models.requests.post")
    def test_search_articles_saves_instance(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "req-xyz"}
        mock_post.return_value = mock_response

        obj = N8nArticlesSearchRequest(question="question text", direct_search=True)
        obj.search_articles()

        self.assertEqual(obj.request_id, "req-xyz")
        self.assertEqual(obj.status, "pending")
        self.assertEqual(obj.environment, "TEST")
        self.assertIsNotNone(obj.pk)

    @override_settings(**WEBHOOK_SETTINGS)
    @patch("ai_assistant.models.requests.post")
    def test_search_articles_propagates_http_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = req_lib.HTTPError("500")
        mock_post.return_value = mock_response

        obj = N8nArticlesSearchRequest(question="q")
        with self.assertRaises(req_lib.HTTPError):
            obj.search_articles()

        self.assertIsNone(obj.pk)


class N8nArticlesSearchCallbackViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = views_module.N8nArticlesSearchCallbackView.as_view()

    def _post(self, payload, token="callback-secret"):
        body = json.dumps(payload).encode()
        request = self.factory.post("/", data=body, content_type="application/json")
        request.headers = {"Authorization": f"Bearer {token}"}
        return request

    def _make_search_request(self, **kwargs):
        defaults = {
            "request_id": "test-req-1",
            "question": "Sample question",
            "environment": "TEST",
            "status": "pending",
        }
        defaults.update(kwargs)
        return N8nArticlesSearchRequest.objects.create(**defaults)

    def test_get_not_allowed(self):
        request = self.factory.get("/")
        request.headers = {}
        response = self.view(request)
        self.assertEqual(response.status_code, 405)

    @override_settings(N8N_ARTICLES_SEARCH_CALLBACK_TOKEN="")
    def test_token_not_configured_returns_503(self):
        response = self.view(self._post({}))
        self.assertEqual(response.status_code, 503)

    @override_settings(**CALLBACK_SETTINGS)
    def test_missing_token_returns_401(self):
        body = json.dumps({}).encode()
        request = self.factory.post("/", data=body, content_type="application/json")
        request.headers = {}
        response = self.view(request)
        self.assertEqual(response.status_code, 401)

    @override_settings(**CALLBACK_SETTINGS)
    def test_invalid_token_returns_401(self):
        response = self.view(self._post({}, token="wrong"))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(_json(response)["error"]["message"], "Invalid bearer token.")

    @override_settings(**CALLBACK_SETTINGS)
    def test_invalid_json_returns_400(self):
        request = self.factory.post("/", data=b"{bad", content_type="application/json")
        request.headers = {"Authorization": "Bearer callback-secret"}
        response = self.view(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(_json(response)["error"]["code"], "invalid_json")

    @override_settings(**CALLBACK_SETTINGS)
    def test_missing_request_id_returns_400(self):
        response = self.view(self._post({"response": "text"}))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(_json(response)["error"]["code"], "missing_field")

    @override_settings(**CALLBACK_SETTINGS)
    def test_unknown_request_id_returns_404(self):
        response = self.view(self._post({"request_id": "no-such-id"}))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(_json(response)["error"]["code"], "not_found")

    @override_settings(**CALLBACK_SETTINGS)
    def test_error_payload_marks_request_failed(self):
        sr = self._make_search_request()

        response = self.view(
            self._post({"request_id": "test-req-1", "error": "n8n timed out"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response)["result"], "failed")

        sr.refresh_from_db()
        self.assertEqual(sr.status, "failed")
        self.assertEqual(sr.response, "n8n timed out")

    @override_settings(**CALLBACK_SETTINGS)
    def test_success_without_case_marks_completed_no_letter(self):
        letter_count_before = Letter.objects.count()
        sr = self._make_search_request()

        response = self.view(
            self._post(
                {
                    "request_id": "test-req-1",
                    "response": "Article content here",
                    "is_foi": "TAK",
                }
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response)["result"], "completed")

        sr.refresh_from_db()
        self.assertEqual(sr.status, "completed")
        self.assertEqual(sr.response, "Article content here")
        self.assertEqual(sr.is_foi, "TAK")
        self.assertEqual(Letter.objects.count(), letter_count_before)

    @override_settings(**CALLBACK_SETTINGS)
    def test_success_empty_response_no_letter_created(self):
        case = CaseFactory()
        self._make_search_request(case=case)

        payload = {"request_id": "test-req-1", "response": "", "is_foi": "NIE"}
        self.view(self._post(payload))

        self.assertEqual(Letter.objects.filter(case=case).count(), 0)

    @override_settings(**CALLBACK_SETTINGS)
    def test_success_creates_letter_for_case(self):
        case = CaseFactory()
        self._make_search_request(case=case, question="Is this FOI?")

        response = self.view(
            self._post(
                {
                    "request_id": "test-req-1",
                    "response": "Here are relevant articles...",
                    "is_foi": "TAK",
                }
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response)["result"], "completed")

        letters = Letter.objects.filter(case=case, genre=Letter.GENRE.ai_message_staff)
        self.assertEqual(letters.count(), 1)
        letter = letters.first()
        self.assertEqual(letter.status, Letter.STATUS.staff)
        self.assertEqual(letter.text, "Here are relevant articles...")
        self.assertTrue(letter.created_by_is_staff)
        self.assertTrue(letter.name.startswith("ASYSTENT AI: "))
        self.assertTrue(letter.html)

    @override_settings(**CALLBACK_SETTINGS)
    def test_letter_name_fallback_when_question_empty(self):
        case = CaseFactory()
        self._make_search_request(case=case, question="")

        self.view(
            self._post(
                {
                    "request_id": "test-req-1",
                    "response": "Some response",
                    "is_foi": "TAK",
                }
            )
        )

        letter = Letter.objects.filter(case=case).first()
        self.assertEqual(letter.name, "ASYSTENT AI: odpowiedź asystenta")

    @override_settings(**CALLBACK_SETTINGS)
    def test_letter_name_contains_question_preview(self):
        case = CaseFactory()
        self._make_search_request(case=case, question="Will this appear in the name?")

        self.view(
            self._post(
                {
                    "request_id": "test-req-1",
                    "response": "Response",
                    "is_foi": "TAK",
                }
            )
        )

        letter = Letter.objects.filter(case=case).first()
        self.assertIn("Will this appear in the name?", letter.name)
