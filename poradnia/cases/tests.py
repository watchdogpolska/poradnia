from cases.factories import CaseFactory
from letters.factories import LetterFactory
from users.factories import UserFactory
from django.test import TestCase
from cases.filters import StaffCaseFilter


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


class StaffCaseFilterTestCase(TestCase):
    def test_hide_permission(self):
        def get_fields(user):
            return StaffCaseFilter(user=user).form.fields
        self.assertNotIn('permission', get_fields(UserFactory(is_staff=True)))
        self.assertNotIn('permission', get_fields(UserFactory(is_staff=False)))
        self.assertIn('permission', get_fields(UserFactory(is_staff=True, is_superuser=True)))

    def get_permission_filter_qs(self, user, **kwargs):
        admin = UserFactory(is_staff=True, is_superuser=True)
        return StaffCaseFilter(user=admin, data={'permission': user.pk}).qs.filter(**kwargs)

    def test_permission_filter(self):
        obj = CaseFactory()
        self.assertFalse(self.get_permission_filter_qs(user=UserFactory(), pk=obj.pk).exists())
        self.assertTrue(self.get_permission_filter_qs(user=obj.created_by, pk=obj.pk).exists())
