from datetime import timedelta

import django
import six
from atom.mixins import AdminTestCaseMixin
from django.contrib.admin.sites import AdminSite
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse_lazy
from django.test import RequestFactory
from django.test.utils import override_settings
from django.utils.timezone import now
from guardian.shortcuts import assign_perm
from test_plus.test import TestCase

from poradnia.cases.admin import CaseAdmin
from poradnia.cases.factories import CaseFactory, PermissionGroupFactory
from poradnia.cases.filters import StaffCaseFilter
from poradnia.cases.forms import CaseCloseForm
from poradnia.cases.models import Case, PermissionGroup
from poradnia.cases.views import CaseListView
from poradnia.letters.factories import LetterFactory
from poradnia.letters.models import Letter
from poradnia.users.factories import UserFactory


class CaseQuerySetTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_for_assign_cant(self):
        self.assertFalse(Case.objects.for_user(self.user).filter(pk=CaseFactory().pk).exists())

    def test_for_user_cant(self):
        self.assertFalse(Case.objects.for_user(self.user).filter(pk=CaseFactory().pk).exists())

    def test_for_user_can_view_all(self):
        assign_perm('cases.can_view_all', self.user)
        self.assertTrue(Case.objects.for_user(self.user).filter(pk=CaseFactory().pk).exists())

    def test_for_assign_can_view_client(self):  # perm set by signal
        self.assertTrue(Case.objects.for_assign(self.user).filter(
            pk=CaseFactory(created_by=self.user).pk).exists())

    def test_for_assign_can_view_created(self):  # perm set by signal
        self.assertTrue(Case.objects.for_assign(self.user).filter(
            pk=CaseFactory(client=self.user).pk).exists())

    def test_with_perm(self):
        CaseFactory.create_batch(size=25)
        with self.assertNumQueries(2):
            qs = Case.objects.with_perm().all()
            for obj in qs:
                list(obj.caseuserobjectpermission_set.all())

    def test_with_record_count(self):
        obj = CaseFactory()
        LetterFactory.create_batch(size=25, case=obj)
        self.assertEqual(Case.objects.filter(pk=obj.pk).with_record_count().get().record_count, 25)

    def test_by_involved_in(self):
        # TODO
        self.assertTrue(True)

    def test_by_msg(self):
        # TODO
        self.assertTrue(True)

    def test_order_for_user(self):
        a = repr(CaseFactory(name="CaseA",
                             last_action=now() + timedelta(days=0),
                             last_send=now() + timedelta(days=+1)))
        b = repr(CaseFactory(name="CaseB",
                             last_action=now() + timedelta(days=+2),
                             last_send=now() + timedelta(days=-1)))
        c = repr(CaseFactory(name="CaseC",
                             last_action=now() + timedelta(days=-1),
                             last_send=now() + timedelta(days=+3)))
        user = UserFactory(is_staff=True)
        self.assertQuerysetEqual(Case.objects.order_for_user(user, True).all(),
                                 [c, a, b])
        self.assertQuerysetEqual(Case.objects.order_for_user(user, False).all(),
                                 [b, a, c])
        user = UserFactory(is_staff=False)
        self.assertQuerysetEqual(Case.objects.order_for_user(user, True).all(),
                                 [b, a, c])
        self.assertQuerysetEqual(Case.objects.order_for_user(user, False).all(),
                                 [c, a, b])


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

    def test_update_counters_last_received_default(self):
        self.object.update_counters()
        self.assertEqual(self.object.last_received, None)

    def _make_letter(self):  # Hack for Travis
        o = LetterFactory(case=self.object, created_by__is_staff=False)
        return Letter.objects.get(pk=o.pk)

    def test_update_counters_last_received_setup(self):
        l = self._make_letter()
        self.object.update_counters()
        self.assertEqual(l.created_on, self.object.last_received)

    def test_update_counters_last_received_update(self):
        self._make_letter()
        self.object.update_counters()
        new = self._make_letter()
        self.object.update_counters()
        self.assertEqual(new.created_on, self.object.last_received)


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
    def __init__(self, methodName='runTest'):
        super(StaffCaseFilterTestCase, self).__init__(methodName)
        if six.PY3:  # In Python 3, assertItemsEqual is named assertCountEqual.
            self.assertItemsEqual = self.assertCountEqual

    def get_filter(self, *args, **kwargs):
        return StaffCaseFilter(queryset=Case.objects.all(),
                               *args, **kwargs)

    def get_permission_filter_qs(self, user, **kwargs):
        admin = UserFactory(is_staff=True, is_superuser=True)
        return self.get_filter(user=admin, data={'permission': user.pk}).qs.filter(**kwargs)

    def test_permission_filter(self):
        obj = CaseFactory()
        self.assertFalse(self.get_permission_filter_qs(user=UserFactory(), pk=obj.pk).exists())
        user = UserFactory(is_staff=True)
        assign_perm('cases.can_view', user, obj)
        self.assertTrue(self.get_permission_filter_qs(user=user, pk=obj.pk).exists())

    def test_form_fields(self):
        su_user = UserFactory(is_staff=True, is_superuser=True)
        self.assertItemsEqual(self.get_filter(user=su_user).form.fields.keys(),
                              ['status',
                               'handled',
                               'id',
                               'client',
                               'name',
                               'has_project',
                               'permission',
                               'o'])
        self.assertItemsEqual(self.get_filter(user=UserFactory(is_staff=True)).form.fields.keys(),
                              ['status',
                               'handled',
                               'id',
                               'client',
                               'name',
                               'has_project',
                               'permission',
                               'o'])


class CaseListViewTestCase(TestCase):
    url = reverse_lazy('cases:list')

    def _test_filtersetclass(self, expect, user):
        self.factory = RequestFactory()
        req = self.factory.get('/')
        req.user = user
        view = CaseListView.as_view()
        resp = view(req)
        view_for_req = resp.context_data['view']
        self.assertEqual(view_for_req.get_filterset_class() == StaffCaseFilter, expect)

    def test_filtersetclass_for_staff(self):
        self._test_filtersetclass(True, UserFactory(is_staff=True))
        self._test_filtersetclass(False, UserFactory(is_staff=False))


class CaseAdminTestCase(TestCase):
    def setUp(self):
        self.site = AdminSite()

    def assertIsValid(self, model_admin, model):  # See django/tests/modeladmin/tests.py#L602
        admin_obj = model_admin(model, self.site)
        if django.VERSION > (1, 9):
            errors = admin_obj.check()
        else:
            errors = admin_obj.check(model)
        expected = []
        self.assertEqual(errors, expected)

    def test_is_valid(self):
        self.assertIsValid(CaseAdmin, Case)

    def test_record_count(self):
        case = CaseFactory()
        LetterFactory.create_batch(size=25, case=case)
        admin_obj = CaseAdmin(Case, AdminSite())
        request = RequestFactory().get(reverse_lazy('admin:cases_case_changelist'))
        request.user = UserFactory(is_staff=True, is_superuser=True)
        qs = admin_obj.get_queryset(request)
        obj = qs.get(pk=case.pk)
        self.assertTrue(hasattr(obj, 'record_count'))
        self.assertEqual(admin_obj.record_count(obj), 25)


class CaseCloseViewTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.object = CaseFactory()
        self.client.login(username=self.user.username, password='pass')

    def test_close_case(self):
        assign_perm('cases.can_close_case', self.user, self.object)
        resp = self.client.post(self.object.get_close_url(), {'notify': True})
        self.assertEqual(
            resp.context['target'].status,
            Case.STATUS.closed)

    def test_close_case_not_permitted(self):
        resp = self.client.get(self.object.get_close_url())
        self.assertEqual(resp.status_code, 403)


class CaseCloseFormTestCase(TestCase):
    form = CaseCloseForm

    def setUp(self):
        self.user = UserFactory()
        self.object = CaseFactory()

    def test_close_notify(self):
        self.form({'notify': False}, user=self.user, instance=self.object).save()
        self.assertEqual(len(mail.outbox), 0)
        self.form({'notify': True}, user=self.user, instance=self.object).save()
        self.assertEqual(len(mail.outbox), 1)


class UserPermissionViewTestCase(TestCase):
    def setUp(self):
        self.actor = UserFactory()
        self.user_with_permission = UserFactory()
        self.object = CaseFactory()
        assign_perm('cases.can_assign', self.actor)
        self.client.login(username=self.actor, password='pass')
        self.url = reverse_lazy('cases:permission_add', kwargs={
            'pk': self.object.pk
        })

    def test_view_loads_correctly(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.object.name)

    def test_invalid_user_used(self):
        resp = self.client.post(self.url, data={'users': [self.user_with_permission.pk],
                                                'permissions': ['can_view', ]})
        self.assertEqual(resp.status_code, 200)

    def test_valid_user_used(self):
        assign_perm('users.can_view_other', self.actor)
        resp = self.client.post(self.url, data={'users': [self.user_with_permission.pk],
                                                'permissions': ['can_view', ]})
        self.assertEqual(resp.status_code, 302)


class CaseGroupPermissionViewTestCase(TestCase):
    def setUp(self):
        self.actor = UserFactory()
        self.user_with_permission = UserFactory(is_staff=True)
        self.object = CaseFactory()
        assign_perm('cases.can_assign', self.actor)
        self.client.login(username=self.actor, password='pass')
        self.url = reverse_lazy('cases:permission_grant', kwargs={
            'pk': self.object.pk
        })

    def test_view_loads_correctly(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.object.name)

    def test_assign_permission(self):
        self.assertFalse(self.user_with_permission.has_perm('can_send_to_client',
                                                            self.object))

        pg = PermissionGroupFactory(permissions=('can_send_to_client',))
        resp = self.client.post(self.url, data={'user': self.user_with_permission.pk,
                                                'group': pg.pk})
        self.assertEqual(resp.status_code, 302)

        self.assertTrue(self.user_with_permission.has_perm('cases.can_send_to_client',
                                                           self.object))


class CaseAdminTestCase(AdminTestCaseMixin, TestCase):
    user_factory_cls = UserFactory
    factory_cls = CaseFactory
    model = Case


class PermissionGroupAdminTestCase(AdminTestCaseMixin, TestCase):
    user_factory_cls = UserFactory
    factory_cls = PermissionGroupFactory
    model = PermissionGroup
