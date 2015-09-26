from django.test import TestCase

from django.core.urlresolvers import reverse_lazy

from django.core import mail

from cases.models import Case
from letters.models import Letter
from users.factories import UserFactory


class NewCaseMixin(object):
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
        self.assertEqual(resp.context_data['form'].fields.keys(), self.fields)


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
