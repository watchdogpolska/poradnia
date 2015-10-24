from cases.factories import CaseFactory
from letters.factories import LetterFactory
from users.factories import UserFactory
from django.test import TestCase
from cases.filters import StaffCaseFilter
from django.core.urlresolvers import reverse_lazy
from cases.models import Case
from django.test.utils import override_settings
from guardian.shortcuts import assign_perm
from django.core.exceptions import PermissionDenied


class CaseTestCase(TestCase):
    def setUp(self):
        self.object = CaseFactory()

    def test_get_edit_url(self):
        self.assertEqual(CaseFactory(pk=50).get_edit_url(), '/sprawy/sprawa-50/edytuj/')

    @override_settings(PORADNIA_EMAIL_INPUT='case-(?P<pk>\d+)@example.com')
    def test_get_by_email(self):
        with self.assertRaises(Case.DoesNotExist):
            Case.get_by_email('case-22@example.com')
            Case.get_by_email('broken@example.com')
        obj = CaseFactory(pk=22)
        obj2 = Case.get_by_email('case-22@example.com')
        self.assertEqual(obj, obj2)

    def test_perm_check(self):
        u1 = UserFactory()
        assign_perm('cases.can_view', u1)

        u2 = UserFactory()
        assign_perm('cases.can_view', u2, self.object)

        self.assertTrue(self.object.perm_check(u1, 'can_view'))
        self.assertTrue(self.object.perm_check(u2, 'can_view'))
        with self.assertRaises(PermissionDenied):
            self.object.perm_check(UserFactory(), 'can_view')

    def test_status_update_initial(self):
        self.assertEqual(self.object.status, Case.STATUS.free)

    def test_status_update_still_open(self):
        assign_perm('cases.can_send_to_client', UserFactory(is_staff=False), self.object)
        self.object.status_update()
        self.assertEqual(self.object.status, Case.STATUS.free)

    def test_status_update_assigned(self):
        assign_perm('cases.can_send_to_client', UserFactory(is_staff=True), self.object)
        self.object.status_update()
        self.assertEqual(self.object.status, Case.STATUS.assigned)

    def test_status_update_closed(self):
        self.object.status = Case.STATUS.closed
        self.object.status_update()
        self.assertEqual(self.object.status, Case.STATUS.closed)
        self.object.status_update(reopen=True)
        self.assertEqual(self.object.status, Case.STATUS.free)


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
        user = UserFactory(is_staff=True)
        assign_perm('cases.can_assign', user)
        self.assertIn('permission', get_fields(user))

    def get_permission_filter_qs(self, user, **kwargs):
        admin = UserFactory(is_staff=True, is_superuser=True)
        return StaffCaseFilter(user=admin, data={'permission': user.pk}).qs.filter(**kwargs)

    def test_permission_filter(self):
        obj = CaseFactory()
        self.assertFalse(self.get_permission_filter_qs(user=UserFactory(), pk=obj.pk).exists())
        self.assertTrue(self.get_permission_filter_qs(user=obj.created_by, pk=obj.pk).exists())

    def test_order_by(self):
        def get_filter(choice='default'):
            return StaffCaseFilter(user=UserFactory()).get_order_by(choice)
        self.assertEqual(get_filter(), ['-deadline', 'status', '-last_send', '-last_action'])
        self.assertEqual(get_filter('status'), ['status'])


class CaseListViewTestCase(TestCase):
    url = reverse_lazy('cases:list')

    def _test_filtersetclass(self, expect, user):
        self.client.login(username=user.username, password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.context['view'].get_filterset_class() == StaffCaseFilter, expect)

    def test_filtersetclass_for_staff(self):
        self._test_filtersetclass(True, UserFactory(is_staff=True))
        self._test_filtersetclass(False, UserFactory(is_staff=False))
