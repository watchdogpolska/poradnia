import email
from datetime import timedelta
from distutils.version import StrictVersion
from os.path import dirname, join

import django_mailbox
import six
from django.test import TestCase
from django.utils.timezone import now
from django_mailbox.models import Mailbox
from guardian.shortcuts import assign_perm

from poradnia.cases.factories import CaseFactory
from poradnia.cases.models import Case
from poradnia.letters.factories import LetterFactory
from poradnia.letters.models import Letter, MessageParser
from poradnia.users.factories import UserFactory


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


class LastQuerySetTestCase(TestCase):
    def setUp(self):
        self.now = now()
        self.case = CaseFactory()

    def test_lr_staff_letter_no_return(self):
        # staff letter no return (no return)
        LetterFactory(case=self.case,
                      created_by__is_staff=True)
        with self.assertRaises(IndexError):
            Letter.objects.case(self.case).last_received()

    def test_lr_new_client_letter_setup(self):
        l = LetterFactory(case=self.case,
                          created_by__is_staff=False)
        self.assertEqual(Letter.objects.case(self.case).last_received(), l)

    def test_lr_new_client_letter_update(self):
        l = LetterFactory(case=self.case,
                          created_by__is_staff=False)
        self.assertEqual(Letter.objects.case(self.case).last_received(), l)
        new = LetterFactory(case=self.case,
                            created_by__is_staff=False)
        self.assertEqual(Letter.objects.case(self.case).last_received(), new)
        t = self.now - timedelta(days=10)
        old = LetterFactory(created_on=t,
                            case=self.case,
                            created_by__is_staff=False)
        old.created_on = t
        old.save()
        self.assertEqual(Letter.objects.case(self.case).last_received(), new)

    def test_lr_new_letter_from_staff(self):
        l = LetterFactory(created_on=self.now + timedelta(days=2),
                          case=self.case,
                          created_by__is_staff=False)
        LetterFactory(created_on=self.now + timedelta(days=10),
                      case=self.case,
                      created_by__is_staff=True)
        self.assertEqual(Letter.objects.case(self.case).last_received(), l)

    def test_last_staff_send(self):
        l = LetterFactory(status='done', case=self.case, created_by__is_staff=True)
        self.assertEqual(Letter.objects.case(self.case).last_staff_send(), l)

        LetterFactory(status='staff', case=self.case, created_by__is_staff=True)
        self.assertEqual(Letter.objects.case(self.case).last_staff_send(), l)

        l2 = LetterFactory(status='done', case=self.case, created_by__is_staff=True)
        self.assertEqual(Letter.objects.case(self.case).last_staff_send(), l2)


class ReceiveEmailTestCase(TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self.mailbox = Mailbox.objects.create(from_email='from@example.com')

    @staticmethod
    def _get_email_object(filename):  # See coddingtonbear/django-mailbox#89
        path = join(dirname(__file__), 'messages', filename)
        msg_content = open(path, 'rb').read()
        if six.PY3:
            return email.message_from_bytes(msg_content)
        else:
            return email.message_from_string(msg_content)

    def get_message(self, filename):
        message = self._get_email_object(filename)
        msg = self.mailbox._process_message(message)
        msg.save()
        return msg

    def test_user_identification(self):
        user = UserFactory(email='user@example.com')
        message = self.get_message('cc_message.eml')
        MessageParser.receive_signal(sender=self.mailbox, message=message)
        self.assertEqual(user, message.letter_set.all()[0].created_by)

    def test_cc_message(self):
        case = CaseFactory(pk=639)
        message = self.get_message('cc_message.eml')
        MessageParser.receive_signal(sender=self.mailbox, message=message)
        self.assertEqual(case, message.letter_set.all()[0].case)

    def test_closed_to_free(self):
        case = CaseFactory(pk=639, status=Case.STATUS.closed)
        message = self.get_message('cc_message.eml')
        MessageParser.receive_signal(sender=self.mailbox, message=message)

        case.refresh_from_db()
        self.assertEqual(case.status, Case.STATUS.free)

    def test_closed_to_assigned(self):
        case = CaseFactory(pk=639, status=Case.STATUS.closed)
        assign_perm('cases.can_send_to_client', UserFactory(is_staff=True), case)
        msg = self.get_message('cc_message.eml')

        MessageParser.receive_signal(sender=self.mailbox, message=msg)

        case.refresh_from_db()
        self.assertEqual(case.status, Case.STATUS.assigned)

    def test_utf8_message(self):
        if StrictVersion(django_mailbox.__version__) <= StrictVersion('4.5.3'):
            self.skipTest("Django-mailbox is lower than required 4.5.3 " +
                          "to UTF-8 filename attachment")
        case = CaseFactory(pk=639)
        message = self.get_message('utf8_message.eml')
        MessageParser.receive_signal(sender=self.mailbox, message=message)

        case.refresh_from_db()
        self.assertEqual(case.status, Case.STATUS.free)
