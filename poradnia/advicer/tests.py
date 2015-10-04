from __future__ import absolute_import

from unittest import skip

from django.core.urlresolvers import reverse, reverse_lazy
from django.test import TestCase

from advicer.models import Advice
from users.factories import StaffFactory, UserFactory

from .factories import AdviceFactory


class PermissionMixin(object):
    def setUp(self):
        super(PermissionMixin, self).setUp()
        self.user = StaffFactory()

    def login(self, username=None):
        self.client.login(username=username or self.user.username, password='pass')

    def test_anonymous_denied(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_normal_user_denied(self):
        self.login(username=UserFactory().username)
        self.test_anonymous_denied()


class TemplateUsedMixin(object):
    def test_template_used(self):
        self.login()
        resp = self.client.get(self.url)
        self.assertTemplateUsed(resp, self.template_name)


class InstanceMixin(object):
    def setUp(self):
        super(InstanceMixin, self).setUp()
        self.instance = AdviceFactory(advicer=self.user)

    def test_contains_subject(self):
        self.login()
        resp = self.client.get(self.url)
        self.assertContains(resp, self.instance.subject)


class AdviceListTestCase(PermissionMixin, TemplateUsedMixin, TestCase):
    url = reverse_lazy('advicer:list')
    template_name = 'advicer/advice_filter.html'

    def test_hide_unvisible(self):
        self.login()
        obj = AdviceFactory(visible=False)
        resp = self.client.get(self.url)
        self.assertNotContains(resp, obj.subject)

    def _show_visible_for(self, **kwargs):
        obj = AdviceFactory(**kwargs)
        resp = self.client.get(self.url)
        self.assertContains(resp, obj.subject)

    def test_show_visible_for_advicer(self):
        self.login()
        self._show_visible_for(advicer=self.user)

    def test_show_visible_for_created_by(self):
        self.login()
        self._show_visible_for(created_by=self.user)


class AdviceUpdateTestCase(InstanceMixin, PermissionMixin, TemplateUsedMixin, TestCase):
    template_name = 'advicer/advice_form.html'

    def setUp(self):
        super(AdviceUpdateTestCase, self).setUp()
        self.instance = AdviceFactory(advicer=self.user)
        self.url = reverse('advicer:update', kwargs={'pk': self.instance.pk})

    def test_contains_subject(self):
        self.login()
        resp = self.client.get(self.url)
        self.assertContains(resp, self.instance.subject)


class AdviceCreateTestCase(PermissionMixin, TemplateUsedMixin, TestCase):
    template_name = 'advicer/advice_form.html'
    url = reverse_lazy('advicer:create')


class AdviceDeleteTestCase(InstanceMixin, PermissionMixin, TemplateUsedMixin, TestCase):
    template_name = 'advicer/advice_confirm_delete.html'

    def setUp(self):
        super(AdviceDeleteTestCase, self).setUp()
        self.instance = AdviceFactory(advicer=self.user)
        self.url = reverse('advicer:delete', kwargs={'pk': self.instance.pk})

    @skip("TODO: Add update field to view")
    def test_field_update(self):
        self.login()
        self.assertTrue(self.instance.visible)
        self.client.post(self.url)  # Perform action
        self.assertFalse(Advice.objects.get(pk=self.instance.pk).visible)

    def test_object_delete(self):
        self.login()
        self.client.post(self.url)
        self.assertFalse(Advice.objects.filter(pk=self.instance.pk).exists())


class AdviceDetailTestCase(InstanceMixin, PermissionMixin, TemplateUsedMixin, TestCase):
    template_name = 'advicer/advice_detail.html'

    def setUp(self):
        super(AdviceDetailTestCase, self).setUp()
        self.url = reverse('advicer:detail', kwargs={'pk': self.instance.pk})
