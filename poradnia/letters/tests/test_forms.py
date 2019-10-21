from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.test import TestCase

from poradnia.cases.models import Case
from poradnia.letters.forms import NewCaseForm
from poradnia.users.factories import UserFactory

try:
    from django.contrib.auth import get_user_model

    User = get_user_model()
except ImportError:
    from django_filters.auth.models import User

REGISTRATION_SUBJECT = "Rejestracja w Poradni Sieci Obywatelskiej - Watchdog Polska"


class AnonymousNewCaseFormMyTests(TestCase):
    form_cls = NewCaseForm
    data = {
        "email_registration": "x123@wykop.pl",
        "name": "My famous subject",
        "text": "Letter text - Lorem ipsum",
        "giodo": "x",
    }
    fields = ["name", "text", "email_registration", "giodo"]

    def get_form_kwargs(self):
        return dict(user=self.user, data=self.data)

    def get_bound(self, **kwargs):
        return NewCaseForm(**self.get_form_kwargs())

    def get_user(self):
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

    def test_send_email_new_case_to_user_with_notify_new_case(self):
        form = self.get_bound()
        form.is_valid()

        staff = User.objects.create(
            username="user",
            email="jack@example.com",
            password="top_secret",
            is_staff=True,
        )

        staff.notify_new_case = True
        staff.save()

        obj = form.save()

        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(self.data["name"], mail.outbox[1].subject)
        self.assertIn(str(obj.created_by), mail.outbox[1].subject)

    def test_fields_compare(self):
        self.assertEqual(list(self.get_bound().fields.keys()), self.fields)

    def test_login_required(self):
        UserFactory(email=self.data["email_registration"])
        form = self.get_bound()
        self.assertIn("email_registration", form.errors)

    def test_login_not_required(self):
        form = self.get_bound()
        self.assertNotIn("email_registration", form.errors)
