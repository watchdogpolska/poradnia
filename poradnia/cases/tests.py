from .factories import CaseFactory
from letters.factories import LetterFactory
from django.test import TestCase


class CaseDetailViewTestCase(TestCase):
    def setUp(self):
        self.object = CaseFactory()
        self.client.login(username=self.object.created_by.username, password='pass')

    def test_can_view(self):
        self.client.get(self.object.get_absolute_url())

    def test_display_letter(self):
        obj = LetterFactory(case=self.object)
        resp = self.client.get(self.object.get_absolute_url())
        self.assertContains(resp, obj.name)

    def test_hide_internal_letter(self):
        obj = LetterFactory(case=self.object, status='staff')
        obj2 = LetterFactory(case=self.object, status='done')
        self.object.created_by.is_staff = False
        self.object.created_by.save()
        resp = self.client.get(self.object.get_absolute_url())
        self.assertNotContains(resp, obj.name)
        self.assertContains(resp, obj2.name)

