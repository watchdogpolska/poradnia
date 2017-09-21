from django.core import mail
from django.core.urlresolvers import reverse, reverse_lazy
from django.test import TestCase
from guardian.shortcuts import assign_perm

from poradnia.cases.factories import CaseFactory
from poradnia.cases.models import Case
from poradnia.letters.factories import LetterFactory
from poradnia.letters.models import Letter
from poradnia.users.factories import UserFactory
from .compat import refresh_from_db


class CaseMixin(object):
    def _add_random_user(self, case, staff=False):
        user = UserFactory(is_staff=staff)
        assign_perm('can_view', user, case)
        return user


class NewCaseMixin(CaseMixin):
    url = reverse_lazy('letters:add')
    template_name = 'letters/form_new.html'
    fields = None

    def assertSendTemplate(self, template_name):
        templates = {msg.extra_headers['Template'] for msg in mail.outbox
                     if 'Template' in msg.extra_headers}
        if template_name in templates:
            return True
        template_list = ", ".join(templates)
        self.fail("Mail with template {name} wasn't send (used {tpls}).".format(name=template_name,
                                                                                tpls=template_list))

    def post(self, data=None):
        return self.client.post(self.url, data=data or self.get_data())

    def get_case(self):
        return Case.objects.filter(name='Lorem ipsum subject example')

    def get_letter(self):
        return Letter.objects.filter(name='Lorem ipsum subject example')

    def test_template_used(self):
        resp = self.client.get(self.url)
        self.assertTemplateUsed(resp, self.template_name)

    def test_field_map(self):
        resp = self.client.get(self.url)
        self.assertEqual(list(resp.context_data['form'].fields.keys()), self.fields)


class NewCaseAnonymousTestCase(NewCaseMixin, TestCase):
    fields = ['name', 'text', 'email_registration', 'giodo']
    post_data = {'attachment_set-INITIAL_FORMS': '0',
                 u'attachment_set-MAX_NUM_FORMS': '1000',
                 u'attachment_set-MIN_NUM_FORMS': '0',
                 u'attachment_set-TOTAL_FORMS': '3',
                 u'email_registration': 'my_email@oh-noes.pl',
                 u'giodo': 'on',
                 u'name': 'Lorem ipsum subject example',
                 u'text': 'Lorem ipsum example text'}

    def get_data(self):
        return self.post_data

    def test_user_registration(self):
        self.post()
        self.assertSendTemplate('users/email_new_user.html')

    def test_user_notification(self):
        self.post()
        self.assertSendTemplate('cases/email/case_registered.txt')

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
        self.assertEqual('Lorem ipsum subject example', obj.name)
        self.assertEqual('Lorem ipsum example text', obj.text)
        self.assertEqual(obj.case.client, obj.created_by)
        self.assertEqual(obj.case.client.email, 'my_email@oh-noes.pl')

    def test_user_registered_fail(self):
        UserFactory(email=self.post_data['email_registration'])
        resp = self.post()
        self.assertFalse(resp.context_data['form'].is_valid())
        self.assertIn('email_registration', resp.context_data['form'].errors)


class AdminNewCaseTestCase(NewCaseMixin, TestCase):
    fields = ['name', 'text', 'client', 'email', 'giodo']

    def get_data(self):
        self.email = UserFactory.build().email
        return {u'attachment_set-0-DELETE': '',
                u'attachment_set-0-attachment': '',
                u'attachment_set-0-id': '',
                u'attachment_set-0-letter': '',
                u'attachment_set-1-DELETE': '',
                u'attachment_set-1-attachment': '',
                u'attachment_set-1-id': '',
                u'attachment_set-1-letter': '',
                u'attachment_set-2-DELETE': '',
                u'attachment_set-2-attachment': '',
                u'attachment_set-2-id': '',
                u'attachment_set-2-letter': '',
                u'attachment_set-INITIAL_FORMS': '0',
                u'attachment_set-MAX_NUM_FORMS': '1000',
                u'attachment_set-MIN_NUM_FORMS': '0',
                u'attachment_set-TOTAL_FORMS': '3',
                u'client-autocomplete': '',
                u'email': self.email,
                u'giodo': 'on',
                u'name': 'Lorem ipsum subject example',
                u'text': 'Lorem ipsum example text'}

    def setUp(self):
        self.user = UserFactory(is_staff=True, is_superuser=True)
        self.client.login(username=self.user.username, password='pass')

    def test_user_registration(self):
        self.post()
        self.assertSendTemplate('users/email_new_user.html')

    def test_user_notification(self):
        self.post()
        self.assertEqual(mail.outbox[1].extra_headers['Template'],
                         'cases/email/case_registered.txt')
        self.assertIn(self.email, mail.outbox[1].to)


class UserNewCaseTestCase(NewCaseMixin, TestCase):
    fields = ['name', 'text']

    def get_data(self):
        return {u'attachment_set-0-DELETE': '',
                u'attachment_set-0-attachment': '',
                u'attachment_set-0-id': '',
                u'attachment_set-0-letter': '',
                u'attachment_set-1-DELETE': '',
                u'attachment_set-1-attachment': '',
                u'attachment_set-1-id': '',
                u'attachment_set-1-letter': '',
                u'attachment_set-2-DELETE': '',
                u'attachment_set-2-attachment': '',
                u'attachment_set-2-id': '',
                u'attachment_set-2-letter': '',
                u'attachment_set-INITIAL_FORMS': '0',
                u'attachment_set-MAX_NUM_FORMS': '1000',
                u'attachment_set-MIN_NUM_FORMS': '0',
                u'attachment_set-TOTAL_FORMS': '3',
                u'name': 'Lorem ipsum subject example',
                u'text': 'Lorem ipsum example text'}

    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password='pass')

    def test_user_self_notify(self):
        self.post()
        self.assertEqual(mail.outbox[0].extra_headers['Template'],
                         'cases/email/case_registered.txt')
        self.assertIn(self.user.email, mail.outbox[0].to)


class AddLetterTestCase(CaseMixin, TestCase):
    post_data = {'attachment_set-0-DELETE': '',
                 'attachment_set-0-attachment': '',
                 'attachment_set-0-id': '',
                 'attachment_set-0-letter': '',
                 'attachment_set-INITIAL_FORMS': '0',
                 'attachment_set-MAX_NUM_FORMS': '1000',
                 'attachment_set-MIN_NUM_FORMS': '0',
                 'attachment_set-TOTAL_FORMS': '1',
                 'name': 'Odp:  Pytanie o dostep do informacji publicznej',
                 'status': 'done',
                 'text': 'XX'}

    def setUp(self):
        self.case = CaseFactory(handled=False)
        self.url = reverse('letters:add', kwargs={'case_pk': self.case.pk})

    def post(self, data=None):
        params = self.post_data.copy()
        params.update(data or {})
        self.client.login(username=self.user.username, password='pass')
        assign_perm('can_add_record', self.user, self.case)
        return self.client.post(self.url, data=params)

    def resp_user(self, staff, can_send_to_client, **kwargs):
        self.user = UserFactory(is_staff=staff)
        if can_send_to_client:
            assign_perm('can_send_to_client', self.user, self.case)
        return self.post(data=kwargs)

    def _test_status_field(self, staff, can_send_to_client, expected, **kwargs):
        self.resp_user(can_send_to_client=can_send_to_client,
                       staff=staff,
                       **kwargs)
        self.assertEqual(Letter.objects.get().status, expected)

    def test_status_field_staff_can_send_to_client_false(self):
        self._test_status_field(staff=True,
                                can_send_to_client=False,
                                expected=Letter.STATUS.staff)

    def test_status_field_user_true(self):
        self._test_status_field(staff=False,
                                can_send_to_client=True,
                                expected=Letter.STATUS.done)

    def test_status_field_user_false(self):
        self._test_status_field(staff=False,
                                can_send_to_client=False,
                                expected=Letter.STATUS.done)

    def test_status_field_staff_can_send(self):
        self._test_status_field(staff=True,
                                can_send_to_client=True,
                                expected=Letter.STATUS.done,
                                send="X")

    def test_status_field_staff_can_send_staff(self):
        self._test_status_field(staff=True,
                                can_send_to_client=True,
                                expected=Letter.STATUS.staff,
                                send_staff="X")

    def test_status_field_staff_project(self):
        self._test_status_field(staff=True,
                                can_send_to_client=True,
                                expected=Letter.STATUS.staff,
                                project="X")

    def _test_email(self, func, status, user_notify, staff_notify=True):
        user_user = self._add_random_user(self.case, staff=False)
        user_staff = self._add_random_user(self.case, staff=True)
        func()
        self.assertEqual(Letter.objects.get().status, status)
        emails = [x.to[0] for x in mail.outbox
                  if x.extra_headers['Template'] == 'letters/email/letter_created.txt']
        self.assertEqual(user_user.email in emails, user_notify)
        self.assertEqual(user_staff.email in emails, staff_notify)

    def test_email_make_done(self):
        self._test_email(self.test_status_field_staff_can_send, Letter.STATUS.done, True)

    def test_email_make_staff(self):
        self._test_email(self.test_status_field_staff_can_send_staff, Letter.STATUS.staff, False)


class ProjectAddLetterTestCase(CaseMixin, TestCase):
    post_data = {'attachment_set-0-DELETE': '',
                 'attachment_set-0-attachment': '',
                 'attachment_set-0-id': '',
                 'attachment_set-0-letter': '',
                 'attachment_set-INITIAL_FORMS': '0',
                 'attachment_set-MAX_NUM_FORMS': '1000',
                 'attachment_set-MIN_NUM_FORMS': '0',
                 'attachment_set-TOTAL_FORMS': '1',
                 'name': 'Odp:  Pytanie o dostep do informacji publicznej',
                 'text': 'XX'}

    def setUp(self):
        self.case = CaseFactory(has_project=False)
        self.url = reverse('letters:add', kwargs={'case_pk': self.case.pk})

    def post(self, data=None):
        params = self.post_data.copy()
        params.update(data or {})
        self.client.login(username=self.user.username, password='pass')
        assign_perm('can_add_record', self.user, self.case)
        return self.client.post(self.url, data=params)

    def resp_user(self, staff, can_send_to_client=False, **kwargs):
        self.user = UserFactory(is_staff=staff)
        if can_send_to_client:
            assign_perm('can_send_to_client', self.user, self.case)
        return self.post(data=kwargs)

    def test_save_non_staff(self):
        self.resp_user(staff=False, save='Yes')
        self.case = refresh_from_db(self.case)
        self.assertEqual(self.case.has_project, False)

    def test_project_voluntier(self):
        self.resp_user(staff=True, can_send_to_client=True, project='Hell yeah!')
        self.case = refresh_from_db(self.case)
        self.assertEqual(self.case.has_project, True)


class SendLetterTestCase(CaseMixin, TestCase):
    note_text = 'Lorem ipsum XYZ123'

    def setUp(self):
        self.object = LetterFactory(status=Letter.STATUS.staff)
        self.url = reverse('letters:send', kwargs={'pk': self.object.pk})
        self.user = UserFactory(is_staff=True, is_superuser=True)
        self.client.login(username=self.user.username, password='pass')

    def test_provide_form(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, self.object)
        self.assertIn('form', resp.context)

    def _test_send(self):
        resp = self.client.post(self.url, data={'comment': self.note_text})
        return resp

    def test_create_a_note(self):
        self._test_send()
        new = Letter.objects.last()
        self.assertNotEqual(new, self.object)
        self.assertEqual(new.status, Letter.STATUS.staff)
        self.assertEqual(new.text, self.note_text)

    def test_notify_staff_about_note(self):
        user1 = self._add_random_user(staff=True, case=self.object.case)
        user2 = self._add_random_user(staff=False, case=self.object.case)
        assign_perm('can_send_to_client', user1, self.object.case)
        self._test_send()

        emails = [x.to[0] for x in mail.outbox
                  if x.extra_headers['Template'] == 'letters/email/letter_drop_a_note.txt']
        self.assertEqual(user1.email in emails, True)
        self.assertEqual(user2.email in emails, False)

    def test_notify_user_about_acceptation(self):
        user1 = self._add_random_user(staff=True, case=self.object.case)
        user2 = self._add_random_user(staff=False, case=self.object.case)

        self._test_send()

        emails = [x.to[0] for x in mail.outbox
                  if x.extra_headers['Template'] == 'letters/email/letter_send_to_client.txt']
        self.assertEqual(user1.email in emails, True)
        self.assertEqual(user2.email in emails, True)

    def test_update_project(self):
        self.object.case.has_project = True
        self.object.case.save()
        self._test_send()
        self.object.case = refresh_from_db(self.object.case)
        self.assertEqual(self.object.case.has_project, False)

    def test_notify_management_to_internal_letter(self):
        user1 = self._add_random_user(staff=True, case=self.object.case)
        user2 = self._add_random_user(staff=True, case=self.object.case)
        user3 = self._add_random_user(staff=True, case=self.object.case)

        assign_perm('cases.can_view_all', user1)
        self._test_send()

        emails = [x.to[0] for x in mail.outbox
                  if x.extra_headers['Template'] == 'letters/email/letter_drop_a_note.txt']
        self.assertEqual(user1.email in emails, True)
        self.assertEqual(user2.email in emails, False)
        self.assertEqual(user3.email in emails, False)
