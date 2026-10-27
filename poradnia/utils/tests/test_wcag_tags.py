from django import forms
from django.template import Context, Template
from django.test import TestCase

from poradnia.utils.ui_mode import UI_MODE_NORMAL, UI_MODE_WCAG


class _NameForm(forms.Form):
    name = forms.CharField()


TEMPLATE = Template("{% load wcag_tags %}{% form_error_summary form %}")


class FormErrorSummaryTestCase(TestCase):
    def render(self, form, ui_mode):
        return TEMPLATE.render(Context({"form": form, "ui_mode": ui_mode}))

    def test_normal_mode_renders_nothing_even_with_errors(self):
        form = _NameForm(data={})
        form.is_valid()
        self.assertTrue(form.errors)

        html = self.render(form, UI_MODE_NORMAL)

        self.assertEqual(html.strip(), "")

    def test_wcag_mode_without_errors_renders_nothing(self):
        form = _NameForm(data={"name": "Jan"})
        form.is_valid()
        self.assertFalse(form.errors)

        html = self.render(form, UI_MODE_WCAG)

        self.assertEqual(html.strip(), "")

    def test_wcag_mode_with_field_error_links_to_the_field(self):
        form = _NameForm(data={})
        form.is_valid()

        html = self.render(form, UI_MODE_WCAG)

        self.assertIn('role="alert"', html)
        self.assertIn(f'href="#{form["name"].id_for_label}"', html)
        self.assertIn(str(form["name"].errors[0]), html)
