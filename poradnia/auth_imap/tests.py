import imaplib
from django.test import TestCase
from mock import patch
from django.contrib.auth import get_user_model

from .checks import check_settings
from .backends import IMAPAuthBackend


class DummyMock(imaplib.IMAP4):
    def __init__(self, *args, **kwargs):
        pass

    def logout(self, *args, **kwargs):
        return


class AuthFailedMock(DummyMock):
    def login(self, *args, **kwargs):
        raise imaplib.IMAP4.error("[AUTHENTICATIONFAILED] Authentication failed.")


class AuthSuccessMock(DummyMock):
    def login(self, *args, **kwargs):
        return ('OK', ['Logged in'])


class IMAPAuthBackendTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(username="login",
                                                    email="joanna@example.com",
                                                    password="X")

    @patch('auth_imap.settings.HOSTS', new={})
    def test_empty_setting(self):
        user = IMAPAuthBackend().authenticate("login@example.com", "X", imap_cls=AuthSuccessMock)
        self.assertEqual(user, None)

    @patch('auth_imap.settings.HOSTS', new={'example.com': {'host': 'example.com'}})
    def test_skip_nonmail(self):
        user = IMAPAuthBackend().authenticate("login", "X")
        self.assertEqual(user, None)

    @patch('auth_imap.settings.HOSTS', new={'example.com': {'host': 'example.com'}})
    def test_auth_success(self):
        user = IMAPAuthBackend().authenticate("login@example.com", "X", imap_cls=AuthSuccessMock)
        self.assertNotEqual(user, None)
        self.assertEqual(user.username, 'login@example.com')
        self.assertEqual(user.email, 'login@example.com')

    @patch('auth_imap.settings.HOSTS', new={'example.com': {'host': 'example.com'}})
    def test_auth_user_create(self):
        user = IMAPAuthBackend().authenticate("login2@example.com", "X", imap_cls=AuthFailedMock)
        self.assertEqual(user, None)

    @patch('auth_imap.settings.HOSTS', new={'example.com': {'host': 'example.com',
                                                            'staff': True}})
    def test_set_staff(self):
        user = IMAPAuthBackend().authenticate("login@example.com", "X", imap_cls=AuthSuccessMock)
        self.assertNotEqual(user, None)
        self.assertEqual(user.is_staff, True)


class CheckTestCase(TestCase):
    def test_checks(self):
        self.assertFalse(check_settings(None))

        with self.settings(AUTHENTICATION_BACKENDS=()):
            self.assertEqual(len(check_settings(None)), 1)
        with self.settings(AUTH_IMAP_HOSTS=None):
            self.assertEqual(len(check_settings(None)), 1)
