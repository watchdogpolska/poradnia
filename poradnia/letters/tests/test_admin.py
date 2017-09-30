from atom.mixins import AdminTestCaseMixin
from test_plus import TestCase

from poradnia.letters.factories import LetterFactory
from poradnia.letters.models import Letter
from poradnia.users.factories import UserFactory


class LetterAdminTestCase(AdminTestCaseMixin, TestCase):
    user_factory_cls = UserFactory
    factory_cls = LetterFactory
    model = Letter
