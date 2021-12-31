import hashlib
import json
import zipfile
from io import BytesIO

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse, reverse_lazy
from guardian.shortcuts import assign_perm

from poradnia.cases.factories import CaseFactory, CaseUserObjectPermissionFactory
from poradnia.cases.models import Case
from poradnia.letters.factories import AttachmentFactory, LetterFactory
from poradnia.letters.models import Letter
from poradnia.letters.settings import LETTER_RECEIVE_SECRET
from poradnia.users.factories import UserFactory
from poradnia.utils.tests.mixins import AssertSendMailMixin

from .compat import refresh_from_db


class CaseMixin(AssertSendMailMixin):
    def _add_random_user(self, case, **kwargs):
        user = UserFactory(**kwargs)
        assign_perm("can_view", user, case)
        return user


class NewCaseMixin(CaseMixin):
    url = reverse_lazy("letters:add")
    template_name = "letters/form_new.html"
    fields = None

    def post(self, data=None):
        return self.client.post(self.url, data=data or self.get_data())

    def get_case(self):
        return Case.objects.filter(name="Lorem ipsum subject example")

    def get_letter(self):
        return Letter.objects.filter(name="Lorem ipsum subject example")

    def test_template_used(self):
        resp = self.client.get(self.url)
        self.assertTemplateUsed(resp, self.template_name)

    def test_field_map(self):
        resp = self.client.get(self.url)
        self.assertEqual(list(resp.context_data["form"].fields.keys()), self.fields)


class NewCaseAnonymousTestCase(NewCaseMixin, TestCase):
    fields = ["name", "text", "email_registration", "giodo"]
    post_data = {
        "attachment_set-INITIAL_FORMS": "0",
        "attachment_set-MAX_NUM_FORMS": "1000",
        "attachment_set-MIN_NUM_FORMS": "0",
        "attachment_set-TOTAL_FORMS": "3",
        "email_registration": "my_email@oh-noes.pl",
        "giodo": "on",
        "name": "Lorem ipsum subject example",
        "text": "Lorem ipsum example text",
    }

    def get_data(self):
        return self.post_data

    def test_user_registration(self):
        self.post()
        self.assertMailSend(
            template="users/email/new_user.txt",
            subject="Rejestracja w Poradni Sieci Obywatelskiej - Watchdog Polska",
        )

    def test_user_notification(self):
        self.post()
        self.assertMailSend(
            template="cases/email/case_registered.txt",
            subject="Sprawa  zarejestrowana w systemie",
        )

    def test_case_exists(self):
        self.post()
        self.assertEqual(self.get_case().count(), 1)

    def test_letter_exists(self):
        self.post()
        self.assertEqual(self.get_letter().count(), 1)

    def test_letter_use_correct_case(self):
        self.post()
        self.assertEqual(self.get_letter().get().case, self.get_case().get())

    def test_object_test(self):
        self.post()
        obj = self.get_letter().get()
        self.assertEqual("Lorem ipsum subject example", obj.name)
        self.assertEqual("Lorem ipsum example text", obj.text)
        self.assertEqual(obj.case.client, obj.created_by)
        self.assertEqual(obj.case.client.email, "my_email@oh-noes.pl")

    def test_user_registered_fail(self):
        UserFactory(email=self.post_data["email_registration"])
        resp = self.post()
        self.assertFalse(resp.context_data["form"].is_valid())
        self.assertIn("email_registration", resp.context_data["form"].errors)


class AdminNewCaseTestCase(NewCaseMixin, TestCase):
    fields = ["name", "text", "client", "email", "giodo"]

    def get_data(self):
        self.email = UserFactory.build().email
        return {
            "attachment_set-0-DELETE": "",
            "attachment_set-0-attachment": "",
            "attachment_set-0-id": "",
            "attachment_set-0-letter": "",
            "attachment_set-1-DELETE": "",
            "attachment_set-1-attachment": "",
            "attachment_set-1-id": "",
            "attachment_set-1-letter": "",
            "attachment_set-2-DELETE": "",
            "attachment_set-2-attachment": "",
            "attachment_set-2-id": "",
            "attachment_set-2-letter": "",
            "attachment_set-INITIAL_FORMS": "0",
            "attachment_set-MAX_NUM_FORMS": "1000",
            "attachment_set-MIN_NUM_FORMS": "0",
            "attachment_set-TOTAL_FORMS": "3",
            "client-autocomplete": "",
            "email": self.email,
            "giodo": "on",
            "name": "Lorem ipsum subject example",
            "text": "Lorem ipsum example text",
        }

    def setUp(self):
        self.user = UserFactory(is_staff=True, is_superuser=True)
        self.client.login(username=self.user.username, password="pass")

    def test_user_registration(self):
        self.post()
        self.assertMailSend(template="users/email/new_user.txt", to=self.email)

    def test_user_notification(self):
        self.post()
        self.assertMailSend(template="cases/email/case_registered.txt", to=self.email)


class UserNewCaseTestCase(NewCaseMixin, TestCase):
    fields = ["name", "text"]

    def get_data(self):
        return {
            "attachment_set-0-DELETE": "",
            "attachment_set-0-attachment": "",
            "attachment_set-0-id": "",
            "attachment_set-0-letter": "",
            "attachment_set-1-DELETE": "",
            "attachment_set-1-attachment": "",
            "attachment_set-1-id": "",
            "attachment_set-1-letter": "",
            "attachment_set-2-DELETE": "",
            "attachment_set-2-attachment": "",
            "attachment_set-2-id": "",
            "attachment_set-2-letter": "",
            "attachment_set-INITIAL_FORMS": "0",
            "attachment_set-MAX_NUM_FORMS": "1000",
            "attachment_set-MIN_NUM_FORMS": "0",
            "attachment_set-TOTAL_FORMS": "3",
            "name": "Lorem ipsum subject example",
            "text": "Lorem ipsum example text",
        }

    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password="pass")

    def test_user_self_notify(self):
        self.post()
        self.assertMailSend(
            template="cases/email/case_registered.txt",
            subject="Sprawa  zarejestrowana w systemie",
            to=self.user.email,
        )


class AddLetterTestCase(CaseMixin, TestCase):
    post_data = {
        "attachment_set-0-DELETE": "",
        "attachment_set-0-attachment": "",
        "attachment_set-0-id": "",
        "attachment_set-0-letter": "",
        "attachment_set-INITIAL_FORMS": "0",
        "attachment_set-MAX_NUM_FORMS": "1000",
        "attachment_set-MIN_NUM_FORMS": "0",
        "attachment_set-TOTAL_FORMS": "1",
        "name": "Odp:  Pytanie o dostep do informacji publicznej",
        "status": "done",
        "text": "*bold* **italic** [link](http://google.pl)",
    }

    def setUp(self):
        self.case = CaseFactory(handled=False)
        self.url = reverse("letters:add", kwargs={"case_pk": self.case.pk})

    def post(self, data=None):
        params = self.post_data.copy()
        params.update(data or {})
        self.client.login(username=self.user.username, password="pass")
        assign_perm("can_add_record", self.user, self.case)
        return self.client.post(self.url, data=params)

    def resp_user(self, staff, can_send_to_client, **kwargs):
        self.user = UserFactory(is_staff=staff)
        if can_send_to_client:
            assign_perm("can_send_to_client", self.user, self.case)
        return self.post(data=kwargs)

    def _test_status_field(self, staff, can_send_to_client, expected, **kwargs):
        self.resp_user(can_send_to_client=can_send_to_client, staff=staff, **kwargs)
        self.assertEqual(Letter.objects.get().status, expected)

    def test_status_field_staff_can_send_to_client_false(self):
        self._test_status_field(
            staff=True, can_send_to_client=False, expected=Letter.STATUS.staff
        )

    def test_status_field_user_true(self):
        self._test_status_field(
            staff=False, can_send_to_client=True, expected=Letter.STATUS.done
        )

    def test_status_field_user_false(self):
        self._test_status_field(
            staff=False, can_send_to_client=False, expected=Letter.STATUS.done
        )

    def test_status_field_staff_can_send(self):
        self._test_status_field(
            staff=True, can_send_to_client=True, expected=Letter.STATUS.done, send="X"
        )

    def test_status_field_staff_can_send_staff(self):
        self._test_status_field(
            staff=True,
            can_send_to_client=True,
            expected=Letter.STATUS.staff,
            send_staff="X",
        )

    def test_status_field_staff_project(self):
        self._test_status_field(
            staff=True,
            can_send_to_client=True,
            expected=Letter.STATUS.staff,
            project="X",
        )

    def _test_email(self, func, status, user_notify, staff_notify=True):
        user_user = self._add_random_user(self.case, is_staff=False)
        user_staff = self._add_random_user(self.case, is_staff=True)
        func()
        self.assertEqual(Letter.objects.get().status, status)
        template = "letters/email/letter_created.txt"
        self.assertMailSend(
            template=template,
            to=user_user.email,
            expected_count=1 if user_notify else 0,
        )
        self.assertMailSend(
            template=template,
            to=user_staff.email,
            expected_count=1 if staff_notify else 0,
        )
        if settings.RICH_TEXT_ENABLED:
            self.assertIn(
                '<p><em>bold</em> <strong>italic</strong> <a href="http://google.pl">link</a></p>',
                mail.outbox[0].body,
            )
        letter = Letter.objects.get()
        self.assertIn(letter.name, mail.outbox[0].subject)
        self.assertIn(str(self.user), mail.outbox[0].subject)

    def test_email_make_done(self):
        self._test_email(
            self.test_status_field_staff_can_send,
            status=Letter.STATUS.done,
            user_notify=True,
            staff_notify=True,
        )

    def test_email_make_staff(self):
        self._test_email(
            self.test_status_field_staff_can_send_staff,
            status=Letter.STATUS.staff,
            user_notify=False,
            staff_notify=True,
        )

    def test_notify_user_with_notify_unassigned_letter(self):
        management_user = UserFactory(notify_unassigned_letter=True)

        self.user = UserFactory(is_staff=True)
        assign_perm("can_add_record", self.user, self.case)
        self.client.login(username=self.user.username, password="pass")

        data = self.post_data.copy()
        data["project"] = "True"

        self.client.post(self.url, data=data)
        self.assertMailSend(to=management_user.email)

    def test_notify_management_if_not_lawyer(self):
        management_user = UserFactory(notify_unassigned_letter=True)

        self.user = UserFactory(is_staff=False)
        assign_perm("can_add_record", self.user, self.case)
        self.client.login(username=self.user.username, password="pass")

        data = self.post_data.copy()

        self.client.post(self.url, data=data)

        self.assertMailSend(to=management_user.email)

        self.user = UserFactory(is_staff=True)
        assign_perm("can_send_to_client", self.user, self.case)

        self.client.post(self.url, data=data)

    def test_not_notify_management_if_has_lawyer(self):
        management_user = UserFactory(notify_unassigned_letter=True)

        self.user = UserFactory(is_staff=False)
        assign_perm("can_add_record", self.user, self.case)
        assign_perm("can_send_to_client", UserFactory(is_staff=True), self.case)
        self.client.login(username=self.user.username, password="pass")

        data = self.post_data.copy()

        self.client.post(self.url, data=data)

        self.assertMailSend(to=management_user.email, expected_count=0)


class ProjectAddLetterTestCase(CaseMixin, TestCase):
    post_data = {
        "attachment_set-0-DELETE": "",
        "attachment_set-0-attachment": "",
        "attachment_set-0-id": "",
        "attachment_set-0-letter": "",
        "attachment_set-INITIAL_FORMS": "0",
        "attachment_set-MAX_NUM_FORMS": "1000",
        "attachment_set-MIN_NUM_FORMS": "0",
        "attachment_set-TOTAL_FORMS": "1",
        "name": "Odp:  Pytanie o dostep do informacji publicznej",
        "text": "XX",
    }

    def setUp(self):
        self.case = CaseFactory(has_project=False)
        self.url = reverse("letters:add", kwargs={"case_pk": self.case.pk})

    def post(self, data=None):
        params = self.post_data.copy()
        params.update(data or {})
        self.client.login(username=self.user.username, password="pass")
        assign_perm("can_add_record", self.user, self.case)
        return self.client.post(self.url, data=params)

    def resp_user(self, staff, can_send_to_client=False, **kwargs):
        self.user = UserFactory(is_staff=staff)
        if can_send_to_client:
            assign_perm("can_send_to_client", self.user, self.case)
        return self.post(data=kwargs)

    def test_save_non_staff(self):
        self.resp_user(staff=False, save="Yes")
        self.case = refresh_from_db(self.case)
        self.assertEqual(self.case.has_project, False)

    def test_project_voluntier(self):
        self.resp_user(staff=True, can_send_to_client=True, project="Hell yeah!")
        self.case = refresh_from_db(self.case)
        self.assertEqual(self.case.has_project, True)


class SendLetterTestCase(CaseMixin, TestCase):
    note_text = "Lorem ipsum XYZ123"

    def assertEmailReceived(self, email, template=None):
        emails = [
            x.to[0]
            for x in mail.outbox
            if not template or template in self._templates_used(x)
        ]
        self.assertIn(email, emails)

    def assertEmailNotReceived(self, email, template=None):
        emails = [
            x.to[0]
            for x in mail.outbox
            if not template or template in self._templates_used(x)
        ]
        self.assertNotIn(email, emails)

    def setUp(self):
        self.object = LetterFactory(status=Letter.STATUS.staff)
        self.url = reverse("letters:send", kwargs={"pk": self.object.pk})
        self.user = UserFactory(is_staff=True, is_superuser=True)
        self.client.login(username=self.user.username, password="pass")

    def test_provide_form(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, self.object)
        self.assertIn("form", resp.context)

    def _test_send(self):
        resp = self.client.post(self.url, data={"comment": self.note_text})
        return resp

    def test_create_a_note(self):
        self._test_send()
        new = Letter.objects.last()
        self.assertNotEqual(new, self.object)
        self.assertEqual(new.status, Letter.STATUS.staff)
        self.assertEqual(new.text, self.note_text)

    def test_notify_staff_about_note(self):
        user1 = self._add_random_user(is_staff=True, case=self.object.case)
        user2 = self._add_random_user(is_staff=False, case=self.object.case)
        assign_perm("can_send_to_client", user1, self.object.case)
        self._test_send()

        template = "letters/email/letter_drop_a_note.txt"
        self.assertMailSend(template=template, to=user1.email)
        self.assertMailSend(template=template, to=user2.email, expected_count=0)

    def test_notify_user_about_acceptation(self):
        user1 = self._add_random_user(is_staff=True, case=self.object.case)
        user2 = self._add_random_user(is_staff=False, case=self.object.case)

        self._test_send()

        template = "letters/email/letter_send_to_client.txt"
        self.assertMailSend(template=template, to=user1.email)
        self.assertMailSend(template=template, to=user2.email)
        self.assertMailSend(to=user2.email)  # avoid double message

    def test_accepted_letter_contains_attachment(self):
        letter = AttachmentFactory(letter=self.object)

        self._test_send()

        self.assertIn(letter.get_full_url(), mail.outbox[0].body)

    def test_update_project(self):
        self.object.case.has_project = True
        self.object.case.save()
        self._test_send()
        self.object.case = refresh_from_db(self.object.case)
        self.assertEqual(self.object.case.has_project, False)

    def test_notify_management_to_internal_if_not_lawyer(self):
        user1 = UserFactory(notify_unassigned_letter=True, is_staff=True)
        user2 = self._add_random_user(is_staff=True, case=self.object.case)
        user3 = self._add_random_user(is_staff=True, case=self.object.case)

        self._test_send()
        template = "letters/email/letter_drop_a_note.txt"
        self.assertMailSend(template=template, expected_count=3)
        self.assertMailSend(template=template, to=user1.email)
        self.assertMailSend(template=template, to=user2.email)
        self.assertMailSend(template=template, to=user3.email)

    def test_not_notify_management_to_internal_if_lawyer_assigned(self):
        user1 = UserFactory(notify_unassigned_letter=True, is_staff=True)
        user2 = self._add_random_user(is_staff=True, case=self.object.case)
        user3 = self._add_random_user(is_staff=True, case=self.object.case)
        assign_perm("can_send_to_client", user2, self.object.case)

        self._test_send()

        template = "letters/email/letter_drop_a_note.txt"
        self.assertMailSend(template=template, expected_count=2)
        self.assertMailSend(template=template, to=user1.email, expected_count=0)
        self.assertMailSend(template=template, to=user2.email)
        self.assertMailSend(template=template, to=user3.email)


class StreamAttachmentViewTestCase(TestCase):
    def setUp(self):
        self.attachment = AttachmentFactory()
        self.url = reverse(
            "letters:attachments_zip",
            kwargs={
                "case_pk": self.attachment.letter.case_id,
                "letter_pk": self.attachment.letter.pk,
            },
        )
        self.user = UserFactory(is_staff=True, is_superuser=True)
        self.client.login(username=self.user.username, password="pass")

    def test_streaming_of_file(self):
        resp = self.client.get(self.url)
        # self.assertContains(resp, self.attacment)
        # self.assertIn('form', resp.context)
        output = BytesIO()
        for chunk in resp.streaming_content:
            output.write(chunk)
        with zipfile.ZipFile(output) as myzip:
            filename = myzip.filelist[0].orig_filename
            self.assertEqual(self.attachment.filename, filename)
            with myzip.open(filename) as myfile:
                archived_file_md5 = self._hash_of_file(myfile)
                original_file_md5 = self._hash_of_file(self.attachment.attachment.file)
                self.assertEqual(archived_file_md5, original_file_md5)

    def _hash_of_file(self, myfile):
        hash_md5 = hashlib.md5()
        for chunk in iter(lambda: myfile.read(4096), b""):
            hash_md5.update(chunk)
        return hash_md5.hexdigest()


class DownloadAttachmentViewTestCase(TestCase):
    def setUp(self):
        self.attachment = AttachmentFactory()
        self.url = self.attachment.get_absolute_url()
        self.user = UserFactory(is_staff=True, is_superuser=True)
        self.client.login(username=self.user.username, password="pass")

    def test_get_file_url(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)


class ReceiveEmailTestCase(TestCase):
    def setUp(self):
        self.url = reverse("letters:webhook")
        self.authenticated_url = "{}?secret={}".format(self.url, LETTER_RECEIVE_SECRET)

    def test_required_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_sample_request(self):
        case = CaseFactory()
        response = self.client.post(
            path=self.authenticated_url, data=self._get_body(case)
        )

        self.assertEqual(response.json()["status"], "OK")

        self.assertEqual(case.record_set.count(), 1)
        letter = case.record_set.all()[0].content_object

        self.assertEqual(
            letter.text, "W dniach 3.07-17.08.2018 r. przebywam na urlopie."
        )
        self.assertEqual(letter.attachment_set.all().count(), 1)

        eml_content = letter.eml.read().decode("utf-8")
        attachment_content = (
            letter.attachment_set.all()[0].attachment.read().decode("utf-8")
        )

        self.assertEqual(eml_content, "12345")
        self.assertEqual(attachment_content, "my-content")

    def test_reopen_case_free(self):
        case = CaseFactory(status=Case.STATUS.closed, handled=True)
        response = self.client.post(
            path=self.authenticated_url, data=self._get_body(case)
        )
        self.assertEqual(response.json()["status"], "OK")
        self.assertEqual(Case.objects.get(pk=case.pk).status, Case.STATUS.free)
        self.assertEqual(Case.objects.get(pk=case.pk).handled, False)

    def test_reopen_case_assigned(self):
        case = CaseFactory(status=Case.STATUS.closed, handled=True)
        CaseUserObjectPermissionFactory(
            content_object=case,
            permission_name="can_send_to_client",
            user__is_staff=True,
        )
        response = self.client.post(
            path=self.authenticated_url, data=self._get_body(case)
        )
        self.assertEqual(response.json()["status"], "OK")
        self.assertEqual(Case.objects.get(pk=case.pk).status, Case.STATUS.assigned)
        self.assertEqual(Case.objects.get(pk=case.pk).handled, False)

    def test_no_valid_email(self):
        response = self.client.post(path=self.authenticated_url, data=self._get_body())
        letter = Letter.objects.first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(letter.case.created_by.email, "new-user@example.com")

    def test_notify_staff_about_user_letter(self):
        case = CaseFactory(client__is_staff=False)
        cuop_user = CaseUserObjectPermissionFactory(
            content_object=case,
            user__is_staff=True,
        )
        cuop_lawyer = CaseUserObjectPermissionFactory(
            content_object=case,
            permission_name="can_send_to_client",
            user__is_staff=True,
        )
        response = self.client.post(
            path=self.authenticated_url, data=self._get_body(case, case.client.email)
        )
        self.assertEqual(response.json()["status"], "OK")

        emails = [x.to[0] for x in mail.outbox]
        self.assertEqual(len(emails), 2)
        self.assertIn(cuop_lawyer.user.email, emails)
        self.assertIn(cuop_user.user.email, emails)
        self.assertNotIn(case.client.email, emails)  # skip notify self

    def test_user_permission_after_create(self):
        user = UserFactory()
        response = self.client.post(
            path=self.authenticated_url, data=self._get_body(from_=user.email)
        )
        self.assertEqual(response.json()["status"], "OK")
        case = Case.objects.get()
        self.assertTrue(
            case.get_users_with_perms().filter(pk=case.created_by.pk).exists()
        )

    def test_refuse_misaddressed_letter(self):
        user = UserFactory()
        response = self.client.post(
            path=self.authenticated_url,
            data=self._get_body(
                from_=user.email, headers={"to": ["some-other-mail@example.com"]}
            ),
        )
        self.assertEqual(response.status_code, 400)
        emails = [x.to[0] for x in mail.outbox]
        self.assertEqual(len(emails), 1)
        self.assertIn(user.email, emails)

    def _get_body(self, case=None, from_=None, headers=None):
        domain = Site.objects.get_current().domain
        manifest = {
            "headers": {
                "cc": [],
                "date": "2018-07-30T11:33:22",
                "from": [from_ or "new-user@example.com"],
                "message_id": "<E1fk6QU-00CPTw-Ey@s50.hekko.net.pl>",
                "subject": "Nowa wiadomość",
                "to": [case.get_email() if case else f"user-b@{domain}"],
                "to+": [
                    "user-b@siecobywatelska.pl",
                    "user-c@siecobywatelska.pl",
                    case.get_email() if case else f"user-b@{domain}",
                ],
                **(headers or {}),
            },
            "text": {
                "content": "W dniach 3.07-17.08.2018 r. przebywam na urlopie.",
                "quote": "",
            },
            "files_count": 1,
        }
        attachments = [SimpleUploadedFile("my-doc.bin", b"my-content")]

        eml = SimpleUploadedFile("my-content.eml", b"12345")

        return {
            "manifest": SimpleUploadedFile(
                "manifest.json", json.dumps(manifest).encode("utf-8")
            ),
            "eml": eml,
            "attachment": attachments,
        }
