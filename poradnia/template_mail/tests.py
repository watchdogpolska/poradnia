from django.template import TemplateDoesNotExist, TemplateSyntaxError, loader
from django.test import TestCase

from poradnia.template_mail.utils import TemplateKey, TemplateMailManager


class TemplateMailManagerTestCase(TestCase):
    def assertEmpty(self, obj):
        obj = list(obj)
        self.assertEqual(len(obj), 0, "{} is not empty".format(obj))

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
