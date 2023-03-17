from datetime import timedelta

from django.conf import settings
from django.test import TestCase
from django.utils.timezone import now

from poradnia.cases.factories import CaseFactory
from poradnia.letters.factories import AttachmentFactory, LetterFactory
from poradnia.letters.models import Letter
from poradnia.users.factories import UserFactory


class QuerySetTestCase(TestCase):
    def _for_user(self, status, exists, is_superuser=False, is_staff=False):
        user = UserFactory(is_superuser=is_superuser, is_staff=is_staff)
        obj = LetterFactory(status=status, case__created_by=user)
        self.assertEqual(
            Letter.objects.for_user(user).filter(pk=obj.pk).exists(), exists
        )

    def test_for_user_admin_done(self):
        self._for_user(
            status=Letter.STATUS.done, exists=True, is_superuser=True, is_staff=True
        )

    def test_for_user_admin_staff(self):
        self._for_user(
            status=Letter.STATUS.staff, exists=True, is_superuser=True, is_staff=True
        )

    def test_for_user_staff_done(self):
        self._for_user(
            status=Letter.STATUS.done, exists=True, is_superuser=False, is_staff=True
        )

    def test_for_user_staff_staff(self):
        self._for_user(
            status=Letter.STATUS.staff, exists=True, is_superuser=False, is_staff=True
        )

    def test_for_user_client_done(self):
        self._for_user(
            status=Letter.STATUS.done, exists=True, is_superuser=False, is_staff=False
        )

    def test_for_user_client_staff(self):
        self._for_user(
            status=Letter.STATUS.staff, exists=False, is_superuser=False, is_staff=False
        )


class AttachmentTestCase(TestCase):
    def setUp(self):
        self.attachment = AttachmentFactory()

    def test_get_full_url(self):
        self.assertTrue(self.attachment.get_full_url().startswith("https://"))


class LastQuerySetTestCase(TestCase):
    def setUp(self):
        self.now = now()
        self.case = CaseFactory()

    def test_lr_staff_letter_no_return(self):
        # staff letter no return (no return)
        LetterFactory(case=self.case, created_by__is_staff=True)
        with self.assertRaises(IndexError):
            Letter.objects.case(self.case).last_received()

    def test_lr_new_client_letter_setup(self):
        l = LetterFactory(case=self.case, created_by__is_staff=False)
        self.assertEqual(Letter.objects.case(self.case).last_received(), l)

    def test_lr_new_client_letter_update(self):
        l = LetterFactory(case=self.case, created_by__is_staff=False)
        self.assertEqual(Letter.objects.case(self.case).last_received(), l)
        new = LetterFactory(case=self.case, created_by__is_staff=False)
        self.assertEqual(Letter.objects.case(self.case).last_received(), new)
        t = self.now - timedelta(days=10)
        old = LetterFactory(created_on=t, case=self.case, created_by__is_staff=False)
        old.created_on = t
        old.save()
        self.assertEqual(Letter.objects.case(self.case).last_received(), new)

    def test_lr_new_letter_from_staff(self):
        l = LetterFactory(
            created_on=self.now + timedelta(days=2),
            case=self.case,
            created_by__is_staff=False,
        )
        LetterFactory(
            created_on=self.now + timedelta(days=10),
            case=self.case,
            created_by__is_staff=True,
        )
        self.assertEqual(Letter.objects.case(self.case).last_received(), l)

    def test_last_staff_send(self):
        l = LetterFactory(status="done", case=self.case, created_by__is_staff=True)
        self.assertEqual(Letter.objects.case(self.case).last_staff_send(), l)

        LetterFactory(status="staff", case=self.case, created_by__is_staff=True)
        self.assertEqual(Letter.objects.case(self.case).last_staff_send(), l)

        l2 = LetterFactory(status="done", case=self.case, created_by__is_staff=True)
        self.assertEqual(Letter.objects.case(self.case).last_staff_send(), l2)


class ModelTestCase(TestCase):
    def test_render_as_html_returns_html(self):
        text = "some text"
        html = "<pre>some_html</pre>"
        letter = LetterFactory(text=text, html=html)
        self.assertEqual(letter.render_as_html(), html)

    def test_render_as_html_decorates_text(self):
        text = "*italic* **bolded**\n# header1\n[link](www.google.pl)"
        html = ""
        letter = LetterFactory(text=text, html=html)
        if settings.RICH_TEXT_ENABLED:
            expected = '<pre><p><em>italic</em> <strong>bolded</strong></p>\n<h1>header1</h1>\n<p><a href="www.google.pl">link</a></p>\n</pre>'
        else:
            expected = "<{tag}><p>{text}</p></{tag}>".format(
                tag="pre", text=text.replace("\n", "<br>")
            )
        self.assertEqual(letter.render_as_html(), expected)
