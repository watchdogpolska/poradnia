from datetime import datetime
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.urls import reverse, reverse_lazy
from tinycontent.models import TinyContent

from config.urls import handler500
from poradnia.users.factories import StaffFactory, UserFactory
from poradnia.utils.messages_catalog import CATALOG


class StaticPagesTestCase(TestCase):
    def test_pages_render(self):
        for name in ("home", "terms", "privacy", "accessibility_statement"):
            with self.subTest(name=name):
                resp = self.client.get(reverse(name))
                self.assertEqual(resp.status_code, 200)

    def test_accessibility_statement_lists_known_exceptions(self):
        resp = self.client.get(reverse("accessibility_statement"))
        self.assertContains(resp, "2.4.3")
        self.assertContains(resp, "4.1.2")

    def test_robots_txt_disallows_private_areas(self):
        resp = self.client.get("/robots.txt")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Disallow: /admin/")
        self.assertContains(resp, "Disallow: /sprawy/")


class ServerErrorPageTestCase(TestCase):
    def _get(self, **request_attrs):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        for attr, value in request_attrs.items():
            setattr(request, attr, value)
        return handler500(request)

    def test_renders_500_page(self):
        resp = self._get()
        self.assertEqual(resp.status_code, 500)
        self.assertIn("Ooops!!! 500", resp.content.decode())

    def test_shows_sentry_reference_when_available(self):
        resp = self._get(sentry={"id": "abc123"})
        self.assertIn("<strong>abc123</strong>", resp.content.decode())


class AdminIndexTestCase(TestCase):
    def test_links_to_both_catalogs(self):
        self.client.force_login(StaffFactory(is_superuser=True))
        resp = self.client.get(reverse("admin:index"))
        self.assertContains(resp, reverse("email_catalog"))
        self.assertContains(resp, reverse("messages_catalog"))


class MessagesCatalogViewTestCase(TestCase):
    url = reverse_lazy("messages_catalog")

    def test_non_staff_redirected_to_login(self):
        self.client.force_login(UserFactory())
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_staff_sees_every_entry_rendered(self):
        self.client.force_login(StaffFactory())
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sum(len(items) for items in resp.context["groups"].values()), len(CATALOG)
        )
        # Like the e-mail catalog, render failures become preview text.
        self.assertNotContains(resp, "BŁĄD RENDEROWANIA")


class TinyContentTemplatesTestCase(TestCase):
    url = reverse_lazy("terms")

    def setUp(self):
        cache.clear()  # get_content_by_name caches blocks by name
        self.editor = StaffFactory(is_superuser=True, is_content_editor=True)

    def _block(self, content):
        # TINYCONTENT_AUTO_INDEX may already have created the block on migrate.
        block, _ = TinyContent.objects.update_or_create(
            name="terms", defaults={"content": content}
        )
        return block

    def test_filled_block_shows_content_and_edit_link_to_editor(self):
        block = self._block("<p>Regulamin</p>")
        self.client.force_login(self.editor)
        resp = self.client.get(self.url)
        self.assertContains(resp, "<p>Regulamin</p>")
        self.assertContains(
            resp, reverse("admin:tinycontent_tinycontent_change", args=[block.pk])
        )

    def test_empty_block_shows_add_link_to_editor(self):
        block = self._block("")
        self.client.force_login(self.editor)
        resp = self.client.get(self.url)
        self.assertContains(
            resp, reverse("admin:tinycontent_tinycontent_change", args=[block.pk])
        )

    def test_no_edit_link_for_regular_user(self):
        block = self._block("<p>Regulamin</p>")
        self.client.force_login(UserFactory())
        resp = self.client.get(self.url)
        self.assertNotContains(
            resp, reverse("admin:tinycontent_tinycontent_change", args=[block.pk])
        )


@patch("poradnia.utils.templatetags.poradnia_tags.datetime")
class DonatePopupTestCase(TestCase):
    """The variant shown depends on the server date: the main popup runs
    Jan 1 - May 2, the alternative one the rest of the year (non-staff only)."""

    main_popup_marker = 'id="popup-container"'
    alternative_popup_marker = 'id="alt-popup-container"'

    def _home(self, mock_datetime, now, user=None):
        mock_datetime.now.return_value = now
        if user:
            self.client.force_login(user)
        return self.client.get(reverse("home"))

    def test_main_popup_inside_campaign_period(self, mock_datetime):
        resp = self._home(mock_datetime, datetime(2026, 3, 15))
        self.assertContains(resp, self.main_popup_marker)
        self.assertNotContains(resp, self.alternative_popup_marker)

    def test_main_popup_on_last_campaign_day(self, mock_datetime):
        resp = self._home(mock_datetime, datetime(2026, 5, 2))
        self.assertContains(resp, self.main_popup_marker)

    def test_alternative_popup_outside_campaign_period(self, mock_datetime):
        resp = self._home(mock_datetime, datetime(2026, 5, 3))
        self.assertNotContains(resp, self.main_popup_marker)
        self.assertContains(resp, self.alternative_popup_marker)

    def test_staff_get_no_alternative_popup(self, mock_datetime):
        resp = self._home(mock_datetime, datetime(2026, 9, 1), user=StaffFactory())
        self.assertNotContains(resp, self.main_popup_marker)
        self.assertNotContains(resp, self.alternative_popup_marker)
