from __future__ import absolute_import

from django.core import mail
from django.core.urlresolvers import reverse_lazy
from django.test import TestCase
from guardian.shortcuts import assign_perm, get_perms

from cases.factories import CaseFactory
from cases.models import Case
from users.factories import UserFactory
from users.forms import TranslatedUserObjectPermissionsForm
from users.forms import UserForm
from users.models import User


class UserTestCase(TestCase):

    def test_get_user_by_get_by_email_or_create(self):
        self.assertEqual(User.objects.count(), 1)
        new_user = User.objects.get_by_email_or_create('sarah@example.com')
        self.assertEqual(User.objects.count(), 2)
        get_user = User.objects.get_by_email_or_create('sarah@example.com')
        self.assertEqual(new_user, get_user)
        self.assertEqual(User.objects.count(), 2)

    def _create_user(self, email, username):
        User.objects.email_to_unique_username(email)
        self.assertEqual(username, username)
        User.objects.create_user(username=username)

    def test_emaTeil_to_username(self):
        self._create_user('example@example.com', 'example_example_com')
        for i in range(1, 11):
            self._create_user('example@example.com', 'example_example_com-' + str(i))
        with self.assertRaises(ValueError):
            self._create_user('example@example.com', 'example_example_com-11')

    def test_login_email(self):  # Test for regresion #204
        max_length = User._meta.get_field('username').max_length
        email = 'very-long-email-which-make-broken-username@example.com'
        self.assertLessEqual(len(User.objects.email_to_unique_username(email)), max_length)

    def test_has_picture(self):
        self.assertTrue(UserFactory().picture)

    def test_has_codename(self):
        self.assertTrue(UserFactory().codename)

    def test_get_codename(self):
        self.assertEqual(User(username="X", codename="ELA").get_codename(), "ELA")
        self.assertEqual(User(username="X").get_codename(), "X")

    def test_get_nicename(self):
        self.assertEqual(User(username="X",
                              first_name="John",
                              last_name="Smith").get_codename(), "John Smith")
        self.assertEqual(User(username="X").get_codename(), "X")


class UserQuerySetTestCase(TestCase):

    def test_for_user_manager(self):
        u1 = User.objects.create(username="X-1")
        u2 = User.objects.create(username="X-2", is_staff=True)
        u3 = User.objects.create(username="X-3", is_staff=True, is_superuser=True)
        qs = User.objects.for_user(u1).registered().all()
        self.assertQuerysetEqual(list(qs), [repr(u1), repr(u2), repr(u3)], ordered=False)
        qs = User.objects.for_user(u2).registered().all()
        self.assertQuerysetEqual(list(qs), [repr(u2), repr(u3)], ordered=False)
        qs = User.objects.for_user(u3).registered().all()
        self.assertQuerysetEqual(list(qs), [repr(u1), repr(u2), repr(u3)], ordered=False)

    def test_with_case_count(self):
        user = UserFactory()
        CaseFactory.create_batch(size=25, client=user)
        self.assertEqual(User.objects.with_case_count().get(pk=user.pk).case_count, 25)
        self.assertEqual(User.objects.with_case_count().get(pk=UserFactory().pk).case_count, 0)

    def test_with_case_count_assigned(self):
        user = UserFactory()
        self.assertEqual(User.objects.with_case_count_assigned().get(pk=user.pk).case_assigned_sum, 0)

        for size, status in [(1, Case.STATUS.free), (2, Case.STATUS.assigned), (3, Case.STATUS.closed)]:
            for obj in CaseFactory.create_batch(size=size, status=status):
                assign_perm('cases.can_view', user, obj)
        self.assertEqual(User.objects.with_case_count_assigned().get(pk=user.pk).case_assigned_free, 1)
        self.assertEqual(User.objects.with_case_count_assigned().get(pk=user.pk).case_assigned_active, 2)
        self.assertEqual(User.objects.with_case_count_assigned().get(pk=user.pk).case_assigned_closed, 3)
        self.assertEqual(User.objects.with_case_count_assigned().get(pk=user.pk).case_assigned_sum, 6)

        for size, status in [(4, Case.STATUS.free), (5, Case.STATUS.assigned), (6, Case.STATUS.closed)]:
            for obj in CaseFactory.create_batch(size=size, status=status):
                assign_perm('cases.can_view', user, obj)
        self.assertEqual(User.objects.with_case_count_assigned().get(pk=user.pk).case_assigned_free, 5)
        self.assertEqual(User.objects.with_case_count_assigned().get(pk=user.pk).case_assigned_active, 7)
        self.assertEqual(User.objects.with_case_count_assigned().get(pk=user.pk).case_assigned_closed, 9)
        self.assertEqual(User.objects.with_case_count_assigned().get(pk=user.pk).case_assigned_sum, 21)

    def _register_email_count(self, notify, count):
        u = User.objects.register_email(email='sarah@example.com', notify=notify)
        self.assertEqual(len(mail.outbox), count)
        self.assertEqual(User.objects.get(email='sarah@example.com'), u)

    def test_register_email_no_notify(self):
        self._register_email_count(notify=True, count=1)

    def test_register_email_notify(self):
        self._register_email_count(notify=False, count=0)


class UserFormTestCase(TestCase):

    def test_has_avatar(self):
        self.assertIn('picture', UserForm().fields)

    def test_codename_visibility(self):
        # Show for staff
        self.assertIn('codename', UserForm(instance=UserFactory(is_staff=True)).fields)
        # Non-show for non-staff
        self.assertNotIn('codename', UserForm(instance=UserFactory(is_staff=False)).fields)
        # Non show for new object
        self.assertNotIn('codename', UserForm().fields)


class UserDetailViewTestCase(TestCase):

    def setUp(self):
        self.object = UserFactory(is_staff=False)

    def login(self, user=None):
        self.client.login(username=(user or self.object).username, password='pass')

    def get(self):
        return self.client.get(self.object.get_absolute_url())

    def own_resp(self):
        self.login()
        return self.get()

    def test_contains_username(self):
        self.assertContains(self.own_resp(), self.object.username)

    def test_contains_assigned_cases(self):
        url = reverse_lazy('cases:list') + '?permission=' + str(self.object.pk)
        self.login()
        self.assertNotContains(self.own_resp(), url)

        user = UserFactory()
        assign_perm('users.can_view_other', user)
        assign_perm('cases.can_assign', user)
        self.login(user=user)
        self.assertContains(self.get(), url)


class UserListViewTestCase(TestCase):
    url = reverse_lazy('users:list')

    def setUp(self):
        self.user_list = UserFactory.create_batch(size=1, is_staff=False)
        self.staff_list = UserFactory.create_batch(size=1, is_staff=True)
        self.object_list = self.user_list + self.staff_list

    def test_permission_access_and_filter(self):
        self.client.login(username=UserFactory().username, password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

        self.client.login(username=UserFactory(is_staff=True).username, password='pass')
        resp = self.client.get(self.url)
        self.assertContains(resp, self.staff_list[0].username)
        self.assertNotContains(resp, self.user_list[0].username)

        user = UserFactory(is_staff=True)
        assign_perm('users.can_view_other', user)
        self.client.login(username=user.username, password='pass')
        resp = self.client.get(self.url)
        self.assertContains(resp, self.object_list[0].username)
        self.assertContains(resp, self.object_list[0].username)

    def test_contains_filter(self):
        self.client.login(username=UserFactory(is_staff=True).username, password='pass')
        resp = self.client.get(self.url)
        self.assertIn('filter', resp.context)

    def get_view(self, **kwargs):
        return self.client.get(self.url, data=kwargs).context_data['view']

    def test_get_is_staff_choice(self):
        self.client.login(username=UserFactory(is_staff=True).username, password='pass')
        self.assertEqual(self.get_view().get_is_staff_choice(), 0)  # Default
        self.assertEqual(self.get_view(is_staff='a').get_is_staff_choice(), 0)  # Non-num
        self.assertEqual(self.get_view(is_staff='5').get_is_staff_choice(), 0)  # Too large
        self.assertEqual(self.get_view(is_staff=1).get_is_staff_choice(), 1)  # Correct

    def _test_get_queryset(self, iss, **kwargs):
        qs = self.get_view(**kwargs).get_queryset()
        qs = qs.filter(pk=UserFactory(is_staff=iss).pk)
        return qs.exists()

    def test_get_queryset_is_staff_choice(self):
        self.client.login(username=UserFactory(is_staff=True, is_superuser=True).username,
                          password='pass')
        # 0 - _
        self.assertTrue(self._test_get_queryset(iss=True))
        self.assertTrue(self._test_get_queryset(iss=False))
        # 1 - is_staff=True
        self.assertTrue(self._test_get_queryset(iss=True, is_staff='1'))
        self.assertFalse(self._test_get_queryset(iss=False, is_staff='1'))
        # 2 - is_staff=False
        self.assertTrue(self._test_get_queryset(iss=False, is_staff='2'))
        self.assertFalse(self._test_get_queryset(iss=True, is_staff='2'))

    def test_get_context_data_is_staff(self):
        self.client.login(username=UserFactory(is_staff=True, is_superuser=True).username,
                          password='pass')
        resp = self.client.get(self.url, data={'is_staff': 1})
        context_data = resp.context_data
        self.assertIn('is_staff', context_data)
        self.assertEqual(context_data['is_staff']['selected'], 1)
        self.assertIn('choices', context_data['is_staff'])


class LoginPageTestCase(TestCase):
    url = reverse_lazy('account_login')

    def test_login_page_integrate(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, '<form ')
        self.assertContains(resp, 'login')
        self.assertContains(resp, 'password')


class TranslatedUserObjectPermissionsFormTestCase(TestCase):
    def setUp(self):
        self.obj = UserFactory()
        self.user = UserFactory()

    def test_delete_all_permissions(self):
        assign_perm('users.change_user', self.user, self.obj)
        self.assertTrue(self.user.has_perm('users.change_user', self.obj))
        form = TranslatedUserObjectPermissionsForm(data={'permissions': ''},
                                                   user=self.user,
                                                   obj=self.obj)
        self.assertTrue(form.is_valid())
        form.save_obj_perms()
        self.assertFalse(self.user.has_perm('users.change_user', self.obj))
        self.assertEqual(get_perms(self.user, self.obj), [])
