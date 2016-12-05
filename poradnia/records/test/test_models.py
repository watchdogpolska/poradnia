from django.test import TestCase

from letters.factories import LetterFactory
from letters.models import Letter
from records.models import Record
from users.factories import UserFactory


class QuerySetTestCase(TestCase):
    def _test_letter_for_user(self, staff, status, res):
        obj = LetterFactory(case__client__is_staff=staff, status=status)
        self.assertEqual(Record.objects.for_user(obj.case.client).filter(object_id=obj.pk).exists(),
                         res)

    def test_for_user_letter(self):
        self._test_letter_for_user(staff=True, status=Letter.STATUS.done, res=True)
        self._test_letter_for_user(staff=True, status=Letter.STATUS.staff, res=True)
        self._test_letter_for_user(staff=False, status=Letter.STATUS.done, res=True)
        self._test_letter_for_user(staff=False, status=Letter.STATUS.staff, res=False)

    def test_for_user_letter_can_view(self):
        obj = LetterFactory()
        self.assertFalse(Record.objects.for_user(UserFactory()).filter(object_id=obj.pk).exists())
