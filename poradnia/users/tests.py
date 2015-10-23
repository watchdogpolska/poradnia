from __future__ import absolute_import
from django.core import mail
from django.test import TestCase
from guardian.shortcuts import assign_perm
from users.factories import UserFactory
from users.models import User
from users.forms import UserForm


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

    def test_email_to_username(self):
        self._create_user('example@example.com', 'example_example_com')
        for i in range(1, 11):
            self._create_user('example@example.com', 'example_example_com-' + str(i))
        with self.assertRaises(ValueError):
            self._create_user('example@example.com', 'example_example_com-11')

    def test_has_picture(self):
        self.assertTrue(UserFactory().picture)


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
