import json
from unittest.mock import MagicMock, patch

import requests as req_lib
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from ai_assistant import views as views_module
from ai_assistant.models import N8nArticlesSearchRequest, N8nCaseTagsRequest
from poradnia.advicer.factories import (
    AdviceFactory,
    AreaFactory,
    InstitutionKindFactory,
    IssueFactory,
    PersonKindFactory,
)
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

SAMPLE_RESPONSE_BRACKET_URLS = (
    "Uzyteczne artykuly w sprawie:\n"
    "- [https://example.com/article-1]\\n\n"
    "**Temat:** Tytuł pierwszego artykułu\\n\n"
    "**Podsumowanie:** Pierwsze podsumowanie.\n"
    "- [https://example.com/article-2]\\n\n"
    "**Temat:** Tytuł drugiego artykułu\\n\n"
    "**Podsumowanie:** Drugie podsumowanie.\n"
)

SAMPLE_PLAIN_TEXT = (
    "Rozumiem, ze opisuje Pan sytuacje. "
    "Ograniczenie wynika z regulaminu serwisu: "
    "https://porady.siecobywatelska.pl/strony/regulamin-poradnictwa/. "
    "Chetnie pomoge."
)


class FormatArticlesHtmlTestCase(SimpleTestCase):
    def _fmt(self, text):
        return views_module._format_articles_html(text)

    def test_empty_string_returns_empty(self):
        self.assertEqual(self._fmt(""), "")

    def test_whitespace_only_returns_empty(self):
        self.assertEqual(self._fmt("   \n  "), "")

    def test_title_only_plain_text_headline(self):
        html = self._fmt("Tylko tytuł")
        self.assertIn("<strong>ASYSTENT AI:</strong>", html)
        self.assertIn("Tylko tytuł", html)
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

    def test_bracket_url_format_also_works(self):
        html = self._fmt(SAMPLE_RESPONSE_BRACKET_URLS)
        self.assertIn('href="https://example.com/article-1"', html)
        self.assertIn('href="https://example.com/article-2"', html)
        self.assertIn("Tytuł pierwszego artykułu", html)
        self.assertIn("<ul>", html)

    def test_literal_backslash_n_stripped_from_url(self):
        html = self._fmt(SAMPLE_RESPONSE_BRACKET_URLS)
        self.assertNotIn(r"]\n", html)
        self.assertNotIn(r"\n", html)

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

    def test_plain_text_has_asystent_ai_headline(self):
        html = self._fmt(SAMPLE_PLAIN_TEXT)
        self.assertIn("<strong>ASYSTENT AI:</strong>", html)

    def test_plain_text_url_becomes_link(self):
        html = self._fmt(SAMPLE_PLAIN_TEXT)
        self.assertIn(
            'href="https://porady.siecobywatelska.pl/strony/regulamin-poradnictwa/"',
            html,
        )
        self.assertIn('target="_blank"', html)
        self.assertIn('rel="noopener noreferrer"', html)

    def test_plain_text_trailing_period_not_in_url(self):
        html = self._fmt(SAMPLE_PLAIN_TEXT)
        self.assertNotIn(
            'href="https://porady.siecobywatelska.pl/strony/regulamin-poradnictwa/."',
            html,
        )

    def test_plain_text_escapes_html(self):
        html = self._fmt("Tekst <script>bad</script> i link https://safe.example.com.")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn('href="https://safe.example.com"', html)

    def test_plain_text_no_url_renders_as_paragraph(self):
        html = self._fmt("Prosty tekst bez linków.")
        self.assertIn("<p>Prosty tekst bez linków.</p>", html)
        self.assertNotIn("<ul>", html)

    def test_plain_text_md_link_label_equals_url(self):
        url = "https://example.com/page"
        html = self._fmt(f"[{url}]({url})")
        self.assertIn(f'href="{url}"', html)
        self.assertIn(f">{url}<", html)
        self.assertIn('target="_blank"', html)
        self.assertIn('rel="noopener noreferrer"', html)

    def test_plain_text_md_link_custom_label(self):
        html = self._fmt("[link](https://example.com/page)")
        self.assertIn('href="https://example.com/page"', html)
        self.assertIn(">link<", html)
        self.assertIn('target="_blank"', html)
        self.assertIn('rel="noopener noreferrer"', html)

    def test_plain_text_bold_temat_becomes_strong(self):
        html = self._fmt("**Temat:** Tytuł artykułu")
        self.assertIn("<strong>Temat:</strong>", html)
        self.assertNotIn("**Temat:**", html)

    def test_plain_text_bold_podsumowanie_becomes_strong(self):
        html = self._fmt("**Podsumowanie:** Opis artykułu")
        self.assertIn("<strong>Podsumowanie:</strong>", html)
        self.assertNotIn("**Podsumowanie:**", html)

    def test_plain_text_bold_with_url_both_converted(self):
        html = self._fmt("**Temat:** Artykuł https://example.com/")
        self.assertIn("<strong>Temat:</strong>", html)
        self.assertIn('href="https://example.com/"', html)

    def test_plain_text_bold_content_is_html_escaped(self):
        html = self._fmt("**<script>alert(1)</script>**")
        self.assertNotIn("<script>", html)
        self.assertIn("<strong>&lt;script&gt;alert(1)&lt;/script&gt;</strong>", html)


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
    def test_search_articles_handles_http_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = req_lib.HTTPError("500")
        mock_post.return_value = mock_response

        obj = N8nArticlesSearchRequest(question="q")
        result = obj.search_articles()

        self.assertFalse(result)
        self.assertEqual(obj.status, "error")
        self.assertIsNotNone(obj.pk)


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


CASE_TAGS_WEBHOOK_URL = "http://n8n.example.com/webhook/case-tags"
CASE_TAGS_WEBHOOK_SETTINGS = {
    "N8N_CASE_TAGS_WEBHOOK": CASE_TAGS_WEBHOOK_URL,
    "N8N_CASE_TAGS_WEBHOOK_TOKEN": "case-tags-secret",
    "APP_MODE": "TEST",
}


class N8nCaseTagsRequestModelTestCase(TestCase):
    @override_settings(
        N8N_CASE_TAGS_WEBHOOK="",
        N8N_CASE_TAGS_WEBHOOK_TOKEN="",
        APP_MODE="TEST",
    )
    def test_send_tags_request_raises_when_unconfigured(self):
        obj = N8nCaseTagsRequest(question="test")
        with self.assertRaises(ImproperlyConfigured):
            obj.send_tags_request()

    @override_settings(**CASE_TAGS_WEBHOOK_SETTINGS)
    @patch("ai_assistant.models.requests.post")
    def test_send_tags_request_sends_correct_payload(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "tag-req-1"}
        mock_post.return_value = mock_response

        issue = IssueFactory(name="Test Issue")
        area = AreaFactory(name="Test Area")
        person_kind = PersonKindFactory(name="Test Person Kind")

        obj = N8nCaseTagsRequest(question="What is the question?")
        obj.send_tags_request()

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], CASE_TAGS_WEBHOOK_URL)
        self.assertEqual(kwargs["json"]["question"], "What is the question?")
        self.assertEqual(kwargs["json"]["environment"], "TEST")
        self.assertEqual(
            kwargs["headers"],
            {
                "Authorization": "Bearer case-tags-secret",
                "Content-Type": "application/json",
            },
        )
        issue_names = [i["name"] for i in kwargs["json"]["issues_list"]]
        self.assertIn("Test Issue", issue_names)
        area_names = [a["name"] for a in kwargs["json"]["areas_list"]]
        self.assertIn("Test Area", area_names)
        person_kind_names = [p["name"] for p in kwargs["json"]["personkind_list"]]
        self.assertIn("Test Person Kind", person_kind_names)

    @override_settings(**CASE_TAGS_WEBHOOK_SETTINGS)
    @patch("ai_assistant.models.requests.post")
    def test_send_tags_request_saves_instance(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "tag-req-xyz"}
        mock_post.return_value = mock_response

        obj = N8nCaseTagsRequest(question="test question")
        obj.send_tags_request()

        self.assertEqual(obj.request_id, "tag-req-xyz")
        self.assertEqual(obj.status, "pending")
        self.assertEqual(obj.environment, "TEST")
        self.assertIsNotNone(obj.pk)

    @override_settings(**CASE_TAGS_WEBHOOK_SETTINGS)
    @patch("ai_assistant.models.requests.post")
    def test_send_tags_request_handles_http_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = req_lib.HTTPError("500")
        mock_post.return_value = mock_response

        obj = N8nCaseTagsRequest(question="q")
        obj.send_tags_request()

        self.assertEqual(obj.status, "error")
        self.assertIsNotNone(obj.pk)

    @override_settings(**CASE_TAGS_WEBHOOK_SETTINGS)
    @patch("ai_assistant.models.requests.post")
    def test_send_tags_request_excludes_inactive_tags(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "tag-req-2"}
        mock_post.return_value = mock_response

        IssueFactory(name="Active Issue")
        IssueFactory(name="Inactive Issue", active=False)

        obj = N8nCaseTagsRequest(question="q")
        obj.send_tags_request()

        _, kwargs = mock_post.call_args
        issue_names = [i["name"] for i in kwargs["json"]["issues_list"]]
        self.assertIn("Active Issue", issue_names)
        self.assertNotIn("Inactive Issue", issue_names)

    @override_settings(**CASE_TAGS_WEBHOOK_SETTINGS)
    @patch("ai_assistant.models.requests.post")
    def test_send_tags_request_links_to_case(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "tag-req-case"}
        mock_post.return_value = mock_response

        case = CaseFactory()
        obj = N8nCaseTagsRequest(question="q", case=case)
        obj.send_tags_request()

        saved = N8nCaseTagsRequest.objects.get(pk=obj.pk)
        self.assertEqual(saved.case, case)

    @override_settings(**CASE_TAGS_WEBHOOK_SETTINGS)
    @patch("ai_assistant.models.requests.post")
    def test_send_tags_request_uses_default_timeout(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "tag-req-timeout"}
        mock_post.return_value = mock_response

        obj = N8nCaseTagsRequest(question="q")
        obj.send_tags_request()

        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["timeout"], 10)


CASE_TAGS_CALLBACK_SETTINGS = {
    "N8N_CASE_TAGS_CALLBACK_TOKEN": "case-tags-callback-secret"
}

_JST_PATCH = "poradnia.teryt.models.JST.objects.filter"


class N8nCaseTagsPayloadValidationTestCase(TestCase):
    """Tests for _validate_case_tags_payload called directly."""

    def setUp(self):
        self.issue = IssueFactory()
        self.area = AreaFactory()
        self.person_kind = PersonKindFactory()
        self.institution_kind = InstitutionKindFactory()

    def _valid(self):
        return {
            "subject": "Temat",
            "summary": "Podsumowanie",
            "institution_kind_id": self.institution_kind.pk,
            "person_kind_id": self.person_kind.pk,
            "jst_id": "02",
            "issue_ids": [self.issue.pk],
            "area_ids": [self.area.pk],
        }

    def _validate(self, payload):
        return views_module._validate_case_tags_payload(payload)

    def test_missing_subject_returns_error(self):
        p = self._valid()
        del p["subject"]
        err = self._validate(p)
        self.assertIsNotNone(err)
        self.assertIn("subject", _json(err)["error"]["message"])

    def test_empty_subject_returns_error(self):
        p = self._valid()
        p["subject"] = "  "
        err = self._validate(p)
        self.assertIsNotNone(err)

    def test_missing_summary_returns_error(self):
        p = self._valid()
        del p["summary"]
        err = self._validate(p)
        self.assertIsNotNone(err)
        self.assertIn("summary", _json(err)["error"]["message"])

    def test_non_integer_institution_kind_id_returns_error(self):
        p = self._valid()
        p["institution_kind_id"] = "x"
        err = self._validate(p)
        self.assertIsNotNone(err)
        self.assertEqual(_json(err)["error"]["code"], "missing_field")

    def test_nonexistent_institution_kind_id_returns_error(self):
        p = self._valid()
        p["institution_kind_id"] = 99999
        err = self._validate(p)
        self.assertIsNotNone(err)
        self.assertEqual(_json(err)["error"]["code"], "invalid_field")

    def test_nonexistent_person_kind_id_returns_error(self):
        p = self._valid()
        p["person_kind_id"] = 99999
        err = self._validate(p)
        self.assertIsNotNone(err)
        self.assertEqual(_json(err)["error"]["code"], "invalid_field")

    def test_missing_jst_id_is_allowed(self):
        p = self._valid()
        del p["jst_id"]
        err = self._validate(p)
        self.assertIsNone(err)

    def test_null_jst_id_is_allowed(self):
        p = self._valid()
        p["jst_id"] = None
        err = self._validate(p)
        self.assertIsNone(err)

    def test_non_string_jst_id_returns_error(self):
        p = self._valid()
        p["jst_id"] = 2
        err = self._validate(p)
        self.assertIsNotNone(err)
        self.assertEqual(_json(err)["error"]["code"], "invalid_field")

    def test_jst_id_too_short_returns_error(self):
        p = self._valid()
        p["jst_id"] = "1"
        err = self._validate(p)
        self.assertIsNotNone(err)
        self.assertEqual(_json(err)["error"]["code"], "invalid_field")

    def test_jst_id_with_letters_returns_error(self):
        p = self._valid()
        p["jst_id"] = "02abc"
        err = self._validate(p)
        self.assertIsNotNone(err)
        self.assertEqual(_json(err)["error"]["code"], "invalid_field")

    def test_nonexistent_jst_id_returns_error(self):
        p = self._valid()
        p["jst_id"] = "9999999"
        err = self._validate(p)
        self.assertIsNotNone(err)
        self.assertEqual(_json(err)["error"]["code"], "invalid_field")

    @patch(_JST_PATCH)
    def test_empty_issue_ids_returns_error(self, mock_filter):
        mock_filter.return_value.exists.return_value = True
        p = self._valid()
        p["issue_ids"] = []
        err = self._validate(p)
        self.assertIsNotNone(err)
        self.assertIn("issue_ids", _json(err)["error"]["message"])

    @patch(_JST_PATCH)
    def test_nonexistent_issue_id_returns_error(self, mock_filter):
        mock_filter.return_value.exists.return_value = True
        p = self._valid()
        p["issue_ids"] = [99999]
        err = self._validate(p)
        self.assertIsNotNone(err)
        self.assertEqual(_json(err)["error"]["code"], "invalid_field")

    @patch(_JST_PATCH)
    def test_empty_area_ids_returns_error(self, mock_filter):
        mock_filter.return_value.exists.return_value = True
        p = self._valid()
        p["area_ids"] = []
        err = self._validate(p)
        self.assertIsNotNone(err)
        self.assertIn("area_ids", _json(err)["error"]["message"])

    @patch(_JST_PATCH)
    def test_nonexistent_area_id_returns_error(self, mock_filter):
        mock_filter.return_value.exists.return_value = True
        p = self._valid()
        p["area_ids"] = [99999]
        err = self._validate(p)
        self.assertIsNotNone(err)
        self.assertEqual(_json(err)["error"]["code"], "invalid_field")

    @patch(_JST_PATCH)
    def test_valid_payload_returns_none(self, mock_filter):
        mock_filter.return_value.exists.return_value = True
        err = self._validate(self._valid())
        self.assertIsNone(err)


class N8nCaseTagsCallbackViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = views_module.N8nCaseTagsCallbackView.as_view()
        self.issue = IssueFactory()
        self.area = AreaFactory()
        self.person_kind = PersonKindFactory()
        self.institution_kind = InstitutionKindFactory()

    def _post(self, payload, token="case-tags-callback-secret"):
        body = json.dumps(payload).encode()
        request = self.factory.post("/", data=body, content_type="application/json")
        request.headers = {"Authorization": f"Bearer {token}"}
        return request

    def _make_tags_request(self, **kwargs):
        defaults = {
            "request_id": "tag-cb-req-1",
            "question": "Sample question",
            "environment": "TEST",
            "status": "pending",
        }
        defaults.update(kwargs)
        return N8nCaseTagsRequest.objects.create(**defaults)

    def _valid_payload(self, request_id="tag-cb-req-1"):
        return {
            "request_id": request_id,
            "subject": "Test subject",
            "summary": "Test summary",
            "institution_kind_id": self.institution_kind.pk,
            "person_kind_id": self.person_kind.pk,
            "jst_id": "02",
            "issue_ids": [self.issue.pk],
            "area_ids": [self.area.pk],
        }

    def test_get_not_allowed(self):
        request = self.factory.get("/")
        request.headers = {}
        response = self.view(request)
        self.assertEqual(response.status_code, 405)

    @override_settings(N8N_CASE_TAGS_CALLBACK_TOKEN="")
    def test_token_not_configured_returns_503(self):
        response = self.view(self._post({}))
        self.assertEqual(response.status_code, 503)

    @override_settings(**CASE_TAGS_CALLBACK_SETTINGS)
    def test_missing_token_returns_401(self):
        body = json.dumps({}).encode()
        request = self.factory.post("/", data=body, content_type="application/json")
        request.headers = {}
        response = self.view(request)
        self.assertEqual(response.status_code, 401)

    @override_settings(**CASE_TAGS_CALLBACK_SETTINGS)
    def test_invalid_token_returns_401(self):
        response = self.view(self._post({}, token="wrong"))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(_json(response)["error"]["message"], "Invalid bearer token.")

    @override_settings(**CASE_TAGS_CALLBACK_SETTINGS)
    def test_missing_request_id_returns_400(self):
        response = self.view(self._post({"subject": "x"}))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(_json(response)["error"]["code"], "missing_field")

    @override_settings(**CASE_TAGS_CALLBACK_SETTINGS)
    def test_unknown_request_id_returns_404(self):
        response = self.view(self._post({"request_id": "no-such-id"}))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(_json(response)["error"]["code"], "not_found")

    @override_settings(**CASE_TAGS_CALLBACK_SETTINGS)
    def test_error_payload_marks_request_failed(self):
        tr = self._make_tags_request()

        response = self.view(
            self._post({"request_id": "tag-cb-req-1", "error": "n8n timed out"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response)["result"], "failed")
        tr.refresh_from_db()
        self.assertEqual(tr.status, "failed")
        self.assertEqual(tr.response, "n8n timed out")

    @override_settings(**CASE_TAGS_CALLBACK_SETTINGS)
    @patch("ai_assistant.views._validate_case_tags_payload", return_value=None)
    def test_success_without_case_marks_completed(self, _validate):
        tr = self._make_tags_request()

        response = self.view(self._post(self._valid_payload()))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response)["result"], "completed")
        tr.refresh_from_db()
        self.assertEqual(tr.status, "completed")

    @override_settings(**CASE_TAGS_CALLBACK_SETTINGS)
    @patch("ai_assistant.views._validate_case_tags_payload", return_value=None)
    def test_success_with_case_no_advice_creates_advice(self, _validate):
        from poradnia.advicer.models import Advice

        case = CaseFactory()
        tr = self._make_tags_request(case=case)

        response = self.view(self._post(self._valid_payload()))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response)["result"], "completed")
        tr.refresh_from_db()
        self.assertEqual(tr.status, "completed")
        advice = Advice.objects.get(case=case)
        self.assertEqual(advice.ai_assistant_tags["subject"], "Test subject")

    @override_settings(**CASE_TAGS_CALLBACK_SETTINGS)
    @patch("ai_assistant.views._validate_case_tags_payload", return_value=None)
    def test_success_updates_advice_ai_assistant_tags(self, _validate):
        case = CaseFactory()
        advice = AdviceFactory(case=case)
        tr = self._make_tags_request(case=case)

        response = self.view(self._post(self._valid_payload()))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response)["result"], "completed")

        advice.refresh_from_db()
        tags = advice.ai_assistant_tags
        self.assertIsNotNone(tags)
        self.assertEqual(tags["subject"], "Test subject")
        self.assertEqual(tags["summary"], "Test summary")
        self.assertEqual(tags["institution_kind"], self.institution_kind.pk)
        self.assertEqual(tags["person_kind"], self.person_kind.pk)
        self.assertEqual(tags["jst"], "02")
        self.assertEqual(tags["issues"], [self.issue.pk])
        self.assertEqual(tags["area"], [self.area.pk])

    @override_settings(**CASE_TAGS_CALLBACK_SETTINGS)
    @patch("ai_assistant.views._validate_case_tags_payload", return_value=None)
    def test_success_stores_response_json_on_request(self, _validate):
        tr = self._make_tags_request()

        self.view(self._post(self._valid_payload()))

        tr.refresh_from_db()
        stored = json.loads(tr.response)
        self.assertEqual(stored["subject"], "Test subject")
        self.assertEqual(stored["issues"], [self.issue.pk])

    @override_settings(**CASE_TAGS_CALLBACK_SETTINGS)
    def test_success_without_jst_id_omits_jst_from_tags(self):
        from poradnia.advicer.models import Advice

        case = CaseFactory()
        tr = self._make_tags_request(case=case)
        payload = self._valid_payload()
        del payload["jst_id"]

        response = self.view(self._post(payload))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response)["result"], "completed")
        advice = Advice.objects.get(case=case)
        self.assertNotIn("jst", advice.ai_assistant_tags)

    @override_settings(**CASE_TAGS_CALLBACK_SETTINGS)
    def test_invalid_jst_id_format_when_present_returns_400(self):
        tr = self._make_tags_request()  # noqa: F841
        payload = self._valid_payload()
        payload["jst_id"] = "bad"

        response = self.view(self._post(payload))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(_json(response)["error"]["code"], "invalid_field")
