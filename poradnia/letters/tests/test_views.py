from django.test import TestCase

from django.core.urlresolvers import reverse_lazy

from django.core import mail

from cases.models import Case
from letters.models import Letter


class NewCaseAnonymousTestCase(TestCase):
    url = reverse_lazy('letters:add')
    template_name = 'letters/form_new.html'
    post_data = {'attachment_set-INITIAL_FORMS': '0',
                 u'attachment_set-MAX_NUM_FORMS': '1000',
                 u'attachment_set-MIN_NUM_FORMS': '0',
                 u'attachment_set-TOTAL_FORMS': '3',
                 u'email_registration': 'my_email@oh-noes.pl',
                 u'giodo': 'on',
                 u'name': 'Lorem ipsum subject example',
                 u'text': 'Lorem ipsum example text'}

    def assertSendTemplate(self, template_name):
        templates = {msg.extra_headers['Template'] for msg in mail.outbox 
                                                   if 'Template' in msg.extra_headers}
        if template_name not in templates:
            template_list = ", ".join(templates)
            self.fail("Mail with template {name} was not send (used {tpls}).".format(name=template_name,
                                                                                     tpls=template_list))

    def post(self):
        return self.client.post(self.url, data=self.post_data)

    def get_case(self):
        return Case.objects.filter(name='Lorem ipsum subject example')

    def get_letter(self):
        return Letter.objects.filter(name='Lorem ipsum subject example')

    def test_template_used(self):
        resp = self.client.get(self.url)
        self.assertTemplateUsed(resp, self.template_name)

    def test_field_map(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.context_data['form'].fields.keys(),
                         ['name', 'text', 'email_registration', 'giodo'])

    def test_user_registration(self):
        self.post()
        self.assertSendTemplate('users/email_new_user.html')

    def test_user_notification(self):
        self.post()
        self.assertSendTemplate('cases/email/case_registered.txt')

    def test_case_exists(self):
        self.post()
        self.assertTrue(self.get_case().count(), 1)

    def test_letter_exists(self):
        self.post()
        self.assertTrue(self.get_letter().count(), 1)

    def test_letter_use_correct_case(self):
        self.post()
        self.assertEqual(self.get_letter().get().case, self.get_case().get())

    def test_letter_compare(self):
        self.post()
        obj = self.get_letter().get()
        self.assertEqual('Lorem ipsum subject example', obj.name)
        self.assertEqual('Lorem ipsum example text', obj.text)
        self.assertEqual(obj.case.client, obj.created_by)
        self.assertEqual(obj.case.client.email, 'my_email@oh-noes.pl')
