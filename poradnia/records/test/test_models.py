from django.test import TestCase

from letters.factories import LetterFactory

from records.models import Record

from letters.models import Letter


class QuerySetTestCase(TestCase):
    def _test_letter_for_user(self, staff, status, res):
        obj = LetterFactory(created_by__is_staff=staff, status=status)
        self.assertEqual(Record.objects.for_user(obj.created_by).filter(pk=obj.pk).exists(), res)

    def test_for_user_letter(self):
        self._test_letter_for_user(staff=True, status=Letter.STATUS.done, res=True)
        self._test_letter_for_user(staff=True, status=Letter.STATUS.staff, res=True)
        self._test_letter_for_user(staff=False, status=Letter.STATUS.done, res=True)
        self._test_letter_for_user(staff=False, status=Letter.STATUS.staff, res=False)
