from django.test import TestCase
from django.urls import reverse
from guardian.shortcuts import assign_perm

from poradnia.ai_assistant.views import _format_articles_html
from poradnia.cases.factories import CaseFactory
from poradnia.letters.factories import LetterFactory
from poradnia.letters.models import Letter
from poradnia.letters.utils import sanitize_html
from poradnia.users.factories import UserFactory

HOSTILE_HTML = (
    "<p>ok</p>"
    '<img src="https://example.com/a.png" onerror="window.pwned=1">'
    '<div hx-on:click="window.pwned=2" hx-get="/x">y</div>'
    "<script>window.pwned=3</script>"
    '<a href="javascript:window.pwned=4">z</a>'
)
HOSTILE_MARKERS = ("onerror", "hx-on", "hx-get", "<script", "javascript:")


class HostileHtmlAssertMixin:
    def assertHtmlIsClean(self, html):
        for marker in HOSTILE_MARKERS:
            self.assertNotIn(marker, html)


class SanitizeHtmlTestCase(HostileHtmlAssertMixin, TestCase):
    def test_removes_hostile_markup(self):
        self.assertHtmlIsClean(sanitize_html(HOSTILE_HTML))

    def test_drops_contents_of_unrendered_elements(self):
        for html in (
            "<style>p { color: red; }</style><p>a</p>",
            '<STYLE type="text/css">p { color: red; }</STYLE ><p>a</p>',
            "<title>Subject</title><p>a</p>",
            "<script>window.pwned=1</script><p>a</p>",
        ):
            with self.subTest(html=html):
                self.assertEqual(sanitize_html(html), "<p>a</p>")

    def test_unclosed_style_drops_rest_like_a_browser(self):
        self.assertEqual(sanitize_html("<p>a</p><style>p { color: red; }"), "<p>a</p>")

    def test_removing_elements_cannot_assemble_a_tag(self):
        cleaned = sanitize_html("<scr<style></style>ipt>window.pwned=1</script>")
        self.assertNotIn("<script", cleaned)

    def test_keeps_pasted_images(self):
        for mime in ("png", "jpeg", "jpg", "gif"):
            with self.subTest(mime=mime):
                html = f'<img src="data:image/{mime};base64,iVBORw0KGgo=" alt="a">'
                self.assertEqual(sanitize_html(html), html)

    def test_removes_unsafe_data_uri_on_images(self):
        for src in (
            "data:image/svg+xml;base64,PHN2Zz4=",
            "data:image/svg+xml,<svg onload=alert(1)>",
            "data:text/html;base64,PHNjcmlwdD4=",
            "data:image/png,not-base64",
            "data:image/png;base64,a<b",
            "DATA:text/html;base64,PHNjcmlwdD4=",
        ):
            with self.subTest(src=src):
                cleaned = sanitize_html(f'<img src="{src}" alt="a">')
                self.assertNotIn("src", cleaned)
                self.assertIn('alt="a"', cleaned)

    def test_removes_data_uri_on_links(self):
        for href in (
            "data:text/html;base64,PHNjcmlwdD4=",
            "data:image/png;base64,iVBORw0KGgo=",
            "DaTa:text/html,x",
            " data:text/html,x",
            "da&#116;a:text/html,x",
            "da&#x74;a:text/html,x",
            "da&#9;ta:text/html,x",
            "da\tta:text/html,x",
            "da\nta:text/html,x",
            "`data:text/html,x",
        ):
            with self.subTest(href=href):
                self.assertNotIn("href", sanitize_html(f'<a href="{href}">z</a>'))

    def test_keeps_ordinary_links_and_images(self):
        for html in (
            '<a href="https://example.com/a?b=1&amp;c=2">z</a>',
            '<a href="mailto:a@example.com">z</a>',
            '<a href="/sprawy/1">z</a>',
            '<img src="https://example.com/a.png">',
        ):
            with self.subTest(html=html):
                self.assertEqual(sanitize_html(html), html)

    def test_removes_attributes_outside_allowlist(self):
        self.assertEqual(
            sanitize_html('<p class="a" id="b" title="c">d</p>'), "<p>d</p>"
        )

    def test_removes_unsafe_css(self):
        for css in (
            "position: fixed",
            "top: 0",
            "z-index: 9999",
            "margin-top: -500px",
            "transform: scale(9)",
            "background: url(https://example.com/a.png)",
            "background-image: url(https://example.com/a.png)",
        ):
            with self.subTest(css=css):
                cleaned = sanitize_html(f'<p style="{css}">a</p>')
                self.assertNotIn(css.split(":")[0], cleaned)
                self.assertNotIn("url(", cleaned)

    def test_keeps_safe_css_next_to_unsafe_css(self):
        cleaned = sanitize_html(
            '<p style="text-align: center; position: fixed;">a</p>'
        )
        self.assertIn("text-align: center", cleaned)
        self.assertNotIn("position", cleaned)

    def test_keeps_editor_formatting(self):
        html = (
            '<p style="text-align: center; line-height: 1.5; padding-left: 40px;">'
            '<span style="background-color: yellow; font-size: 18pt;">a</span></p>'
        )
        self.assertEqual(sanitize_html(html), html)

    def test_keeps_editor_table(self):
        html = (
            '<table style="border-collapse: collapse; width: 100%;" border="1">'
            '<thead><tr><th scope="col">a</th></tr></thead>'
            '<tbody><tr><td style="width: 50%;" colspan="2">b</td></tr></tbody>'
            "</table>"
        )
        self.assertEqual(sanitize_html(html), html)

    def test_keeps_ai_assistant_markup(self):
        html = _format_articles_html(
            "Tytul\n- [https://example.com/a]\n**Autor:** Jan\n"
        )
        self.assertIn('target="_blank"', html)
        self.assertEqual(sanitize_html(html), html)


class LetterFormsSanitizeTestCase(HostileHtmlAssertMixin, TestCase):
    def setUp(self):
        self.user = UserFactory(is_staff=False)
        self.case = CaseFactory(client=self.user)
        assign_perm("can_view", self.user, self.case)
        assign_perm("can_add_record", self.user, self.case)
        self.client.force_login(self.user)

    def test_add_letter_sanitizes_direct_post(self):
        self.client.post(
            reverse("letters:add", kwargs={"case_pk": self.case.pk}),
            {"name": "hostile", "html": HOSTILE_HTML},
        )
        letter = Letter.objects.get(name="hostile")
        self.assertHtmlIsClean(letter.html)
        self.assertIn("<p>ok</p>", letter.html)

    def test_edit_letter_sanitizes_direct_post(self):
        assign_perm("can_change_own_record", self.user, self.case)
        letter = LetterFactory(case=self.case, created_by=self.user, html="<p>a</p>")
        self.client.post(
            letter.get_edit_url(),
            {
                "name": "hostile",
                "html": HOSTILE_HTML,
                "attachment_set-TOTAL_FORMS": 0,
                "attachment_set-INITIAL_FORMS": 0,
                "attachment_set-MAX_NUM_FORMS": 1000,
            },
        )
        letter.refresh_from_db()
        self.assertEqual(letter.name, "hostile")
        self.assertHtmlIsClean(letter.html)


class StoredLetterRenderTestCase(HostileHtmlAssertMixin, TestCase):
    """Rows saved before the forms sanitised their input stay raw in the DB."""

    def setUp(self):
        self.letter = LetterFactory(html=HOSTILE_HTML, status=Letter.STATUS.done)

    def test_case_page_sanitizes_stored_html(self):
        staff = UserFactory(is_staff=True)
        assign_perm("can_view", staff, self.letter.case)
        self.client.force_login(staff)
        resp = self.client.get(self.letter.case.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "<p>ok</p>")
        self.assertNotContains(resp, "window.pwned=1")
        self.assertNotContains(resp, "window.pwned=2")
        self.assertNotContains(resp, "<script>window.pwned=3")
        self.assertNotContains(resp, "javascript:window.pwned=4")

    def test_render_as_html_sanitizes_stored_html(self):
        self.assertHtmlIsClean(self.letter.render_as_html())
