from django.template import TemplateDoesNotExist, TemplateSyntaxError, loader
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse_lazy
from django.utils.html import escape

from poradnia.template_mail.email_catalog import CATALOG
from poradnia.template_mail.utils import TemplateKey, TemplateMailManager
from poradnia.users.factories import StaffFactory, UserFactory


class TemplateMailManagerTestCase(TestCase):
    def assertEmpty(self, obj):
        obj = list(obj)
        self.assertEqual(len(obj), 0, f"{obj} is not empty")

    def _throws_template_error(self, template):
        try:
            txt = loader.get_template(template.txt_path)
            if template.html_path or True:
                # html_path is optional for now
                html = loader.get_template(template.html_path)
            return None
        except (TemplateDoesNotExist, TemplateSyntaxError) as e:
            return e

    def test_all_enums_mapped(self):
        self.assertEqual(set(TemplateMailManager.TEMPLATE_MAP.keys()), set(TemplateKey))

    def test_maps_all_keys_to_valid_templates(self):
        templates = TemplateMailManager.TEMPLATE_MAP
        ident_error = {
            key: self._throws_template_error(value) for key, value in templates.items()
        }
        self.assertEmpty({(key, err) for key, err in ident_error.items() if err})


class EmailCatalogViewTestCase(TestCase):
    url = reverse_lazy("email_catalog")

    def test_anonymous_redirected_to_login(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_non_staff_redirected_to_login(self):
        self.client.force_login(UserFactory())
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_staff_sees_every_entry_rendered(self):
        self.client.force_login(StaffFactory())
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        for entry in CATALOG:
            self.assertContains(resp, escape(entry.title))
        # The view turns render failures into preview text instead of raising,
        # so a 200 alone doesn't prove the templates render.
        self.assertNotContains(resp, "BŁĄD RENDEROWANIA")
        self.assertNotContains(resp, "brak szablonu")


class EmailCatalogTemplatesTestCase(TestCase):
    """Renders each catalog template directly, so a broken one fails with its
    own name and exception instead of a marker buried in the catalog page."""

    def test_every_template_renders_with_its_preview_context(self):
        for entry in CATALOG:
            templates = (
                entry.txt_template,
                entry.html_template,
                entry.subject_template,
            )
            for template_name in filter(None, templates):
                with self.subTest(key=entry.key, template=template_name):
                    self.assertTrue(render_to_string(template_name, entry.context()))
