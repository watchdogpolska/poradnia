from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from poradnia.utils.middleware import UiModeMiddleware
from poradnia.utils.ui_mode import (
    UI_MODE_COOKIE_NAME,
    UI_MODE_NORMAL,
    UI_MODE_WCAG,
    get_ui_mode,
    resolve_ui_mode,
)


class ResolveUiModeTestCase(TestCase):
    def test_valid_values_pass_through(self):
        self.assertEqual(resolve_ui_mode(UI_MODE_NORMAL), UI_MODE_NORMAL)
        self.assertEqual(resolve_ui_mode(UI_MODE_WCAG), UI_MODE_WCAG)

    def test_invalid_value_falls_back_to_normal(self):
        self.assertEqual(resolve_ui_mode("something-else"), UI_MODE_NORMAL)

    def test_missing_value_falls_back_to_normal(self):
        self.assertEqual(resolve_ui_mode(None), UI_MODE_NORMAL)


class GetUiModeTestCase(TestCase):
    def test_default_outside_any_request(self):
        # No middleware has run in this test, so the ContextVar should still
        # be sitting at its declared default - this is what makes Celery
        # tasks/management commands/email rendering safe without extra code.
        self.assertEqual(get_ui_mode(), UI_MODE_NORMAL)


class UiModeMiddlewareTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _run_middleware(self, request):
        seen = {}

        def get_response(req):
            seen["ui_mode_during_request"] = get_ui_mode()
            return "sentinel-response"

        middleware = UiModeMiddleware(get_response)
        middleware(request)
        return seen["ui_mode_during_request"]

    def test_missing_cookie_resolves_to_normal(self):
        request = self.factory.get("/")
        seen_mode = self._run_middleware(request)
        self.assertEqual(request.ui_mode, UI_MODE_NORMAL)
        self.assertEqual(seen_mode, UI_MODE_NORMAL)

    def test_valid_wcag_cookie_resolves_to_wcag(self):
        request = self.factory.get("/")
        request.COOKIES[UI_MODE_COOKIE_NAME] = UI_MODE_WCAG
        seen_mode = self._run_middleware(request)
        self.assertEqual(request.ui_mode, UI_MODE_WCAG)
        self.assertEqual(seen_mode, UI_MODE_WCAG)

    def test_invalid_cookie_resolves_to_normal(self):
        request = self.factory.get("/")
        request.COOKIES[UI_MODE_COOKIE_NAME] = "garbage"
        seen_mode = self._run_middleware(request)
        self.assertEqual(request.ui_mode, UI_MODE_NORMAL)
        self.assertEqual(seen_mode, UI_MODE_NORMAL)

    def test_contextvar_is_reset_after_the_request(self):
        request = self.factory.get("/")
        request.COOKIES[UI_MODE_COOKIE_NAME] = UI_MODE_WCAG
        self._run_middleware(request)
        self.assertEqual(get_ui_mode(), UI_MODE_NORMAL)


class UiModeSwitchViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("ui_mode_switch")

    def test_get_is_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_switching_to_wcag_sets_cookie_and_redirects(self):
        response = self.client.post(self.url, {"mode": UI_MODE_WCAG, "next": "/"})
        self.assertRedirects(response, "/")
        self.assertEqual(response.cookies[UI_MODE_COOKIE_NAME].value, UI_MODE_WCAG)

    def test_switching_to_normal_sets_cookie(self):
        response = self.client.post(self.url, {"mode": UI_MODE_NORMAL, "next": "/"})
        self.assertEqual(response.cookies[UI_MODE_COOKIE_NAME].value, UI_MODE_NORMAL)

    def test_invalid_mode_is_rejected(self):
        response = self.client.post(self.url, {"mode": "bogus", "next": "/"})
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(UI_MODE_COOKIE_NAME, response.cookies)

    def test_missing_next_defaults_to_root(self):
        response = self.client.post(self.url, {"mode": UI_MODE_WCAG})
        self.assertRedirects(response, "/")

    def test_unsafe_next_host_is_rejected(self):
        response = self.client.post(
            self.url,
            {"mode": UI_MODE_WCAG, "next": "https://evil.example/phish"},
        )
        self.assertRedirects(response, "/")


class BaseTemplateWcagModeTestCase(TestCase):
    """base.html's M1 additions (F001 main/skip-link, F002 messages live
    region) must be purely additive: identical normal-mode output, new
    markup only in WCAG mode - see logs/wcag/plan/ui-mode-design.md §6."""

    def setUp(self):
        self.client = Client()

    def test_normal_mode_has_neither(self):
        response = self.client.get("/")
        content = response.content.decode()
        self.assertNotIn("wcag-skip-link", content)
        self.assertNotIn('<main id="main-content">', content)

    def test_wcag_mode_has_skip_link_and_main_landmark(self):
        self.client.cookies[UI_MODE_COOKIE_NAME] = UI_MODE_WCAG
        response = self.client.get("/")
        content = response.content.decode()
        self.assertIn('class="wcag-skip-link"', content)
        self.assertIn('<main id="main-content">', content)
