from django.template.loader import render_to_string
from django.test import TestCase
from teryt_tree.factories import JednostkaAdministracyjnaFactory

from poradnia.advicer.factories import AdviceFactory
from poradnia.cases.factories import CaseFactory
from poradnia.teryt.models import JST
from poradnia.users.factories import UserFactory


class JSTDetailViewTestCase(TestCase):
    def setUp(self):
        self.jst = JST.objects.get(pk=JednostkaAdministracyjnaFactory().pk)
        self.user = UserFactory(is_superuser=True)
        self.client.force_login(self.user)

    def test_lists_advices_and_cases_in_area(self):
        case = CaseFactory()
        advice = AdviceFactory(case=case, jst_id=self.jst.pk)
        resp = self.client.get(self.jst.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, advice.get_absolute_url())
        self.assertContains(resp, case.get_absolute_url())

    def test_empty_area_shows_no_objects(self):
        resp = self.client.get(self.jst.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Brak pozycji.", count=2)

    def test_lists_have_no_empty_heading(self):
        # The page heads each list with its own <h3>, so _list.html gets no
        # title and must not emit an empty <h2> (WCAG 1.3.1 / 2.4.6).
        resp = self.client.get(self.jst.get_absolute_url())
        self.assertNotContains(resp, "<h2></h2>")

    def test_excludes_advices_from_other_areas(self):
        other_jst = JednostkaAdministracyjnaFactory()
        advice = AdviceFactory(jst_id=other_jst.pk)
        resp = self.client.get(self.jst.get_absolute_url())
        self.assertNotContains(resp, advice.get_absolute_url())


class ListTemplateTestCase(TestCase):
    def test_title_renders_as_heading(self):
        html = render_to_string("_list.html", {"title": "Porady", "object_list": []})
        self.assertInHTML("<h2>Porady</h2>", html)
