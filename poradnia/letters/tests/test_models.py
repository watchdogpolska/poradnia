from django.test import TestCase

from letters.models import Letter
from letters.factories import LetterFactory
from users.factories import UserFactory


class QuerySetTestCase(TestCase):
    def _for_user(self, status, exists, is_superuser=False, is_staff=False):
        user = UserFactory(is_superuser=is_superuser, is_staff=is_staff)
        obj = LetterFactory(status=status, case__created_by=user)
        self.assertEqual(Letter.objects.for_user(user).filter(pk=obj.pk).exists(), exists)

    def test_for_user_admin_done(self):
        self._for_user(status=Letter.STATUS.done,
                       exists=True,
                       is_superuser=True,
                       is_staff=True)

    def test_for_user_admin_staff(self):
        self._for_user(status=Letter.STATUS.staff,
                       exists=True,
                       is_superuser=True,
                       is_staff=True)

    def test_for_user_staff_done(self):
        self._for_user(status=Letter.STATUS.done,
                       exists=True,
                       is_superuser=False,
                       is_staff=True)

    def test_for_user_staff_staff(self):
        self._for_user(status=Letter.STATUS.staff,
                       exists=True,
                       is_superuser=False,
                       is_staff=True)

    def test_for_user_client_done(self):
        self._for_user(status=Letter.STATUS.done,
                       exists=True,
                       is_superuser=False,
                       is_staff=False)

    def test_for_user_client_staff(self):
        self._for_user(status=Letter.STATUS.staff,
                       exists=False,
                       is_superuser=False,
                       is_staff=False)
