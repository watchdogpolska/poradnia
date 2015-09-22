from django.test import TestCase

from django.core import mail
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    from django_filters.auth.models import User

from django.contrib.auth.models import AnonymousUser, Permission
from letters.forms import NewCaseForm
from cases.models import Case, CaseUserObjectPermission
from django.contrib.contenttypes.models import ContentType

REGISTRATION_SUBJECT = 'Rejestracja w Poradni Sieci Obywatelskiej - Watchdog Polska'


class AnonymousNewCaseFormMyTests(TestCase):
    form_cls = NewCaseForm
    data = {'email_registration': 'x123@wykop.pl',
            'name': 'My famous subject',
            'text': 'Letter text - Lorem ipsum',
            'giodo': 'x'}
    fields = ['name', 'text', 'email_registration', 'giodo']

    def get_form_kwargs(self):
        return dict(user=self.user, data=self.data)

    def get_bound(self):
        return NewCaseForm(**self.get_form_kwargs())

    def get_user(self):
        # return User.objects.create_user(username='user',
        #                                 email='jack@example.com',
        #                                 password='top_secret')
        return AnonymousUser()

    def setUp(self):
        self.user = self.get_user()

    def test_valid(self):
        self.assertTrue(self.get_bound().is_valid())

    def test_create_case(self):
        form = self.get_bound()
        form.is_valid()

        self.assertEqual(Case.objects.count(), 0)
        form.save()
        self.assertEqual(Case.objects.count(), 1)

    def test_user_register(self):
        form = self.get_bound()
        form.is_valid()

        u_count = User.objects.count()
        form.save()
        self.assertEqual(User.objects.count() - u_count, 1)

    def test_send_email(self):
        form = self.get_bound()
        form.is_valid()
        form.save()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(REGISTRATION_SUBJECT, mail.outbox[0].subject)
        self.assertIn('x123@wykop.pl', mail.outbox[0].to)

    def test_send_email_new_case_to_staff(self):
        form = self.get_bound()
        form.is_valid()

        staff = User.objects.create(username='user',
                                    email='jack@example.com',
                                    password='top_secret',
                                    is_staff=True)
        content_type = ContentType.objects.get_for_model(Case)
        perm = Permission.objects.get(codename='can_view_all', content_type=content_type)
        staff.user_permissions.add(perm)
        staff.save()
        # CaseUserObjectPermission.objects.create(user=staff, permission=perm)

        obj = form.save()

        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(self.data['name'], mail.outbox[1].subject)
        self.assertIn(unicode(obj.created_by), mail.outbox[1].subject)

    def fields_compare(self):
        self.assertEqual(self.get_bound().fields.keys(), self.fields)
