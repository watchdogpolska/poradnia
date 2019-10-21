import datetime

from atom.ext.guardian.tests import PermissionStatusMixin
from atom.mixins import AdminTestCaseMixin
from django.urls import reverse, reverse_lazy
from guardian.shortcuts import assign_perm
from test_plus.test import TestCase

from poradnia.advicer.models import Advice
from poradnia.users.factories import StaffFactory, UserFactory

from .factories import AdviceFactory, IssueFactory

from django.urls import reverse


class PermissionMixin(object):
    def setUp(self):
        super(PermissionMixin, self).setUp()
        self.user = StaffFactory()

    def login(self, username=None):
        self.client.login(username=username or self.user.username, password="pass")

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

    def test_hide_unvisible(self):
        self.login()
        resp = self.client.get(
            AdviceFactory(advicer=self.user, visible=False).get_absolute_url()
        )
        self.assertEqual(resp.status_code, 404)


class AdviceListTestCase(PermissionMixin, TemplateUsedMixin, TestCase):
    url = reverse_lazy("advicer:list")
    template_name = "advicer/advice_filter.html"

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
    template_name = "advicer/advice_form.html"

    def setUp(self):
        super(AdviceUpdateTestCase, self).setUp()
        self.instance = AdviceFactory(advicer=self.user)
        self.url = reverse("advicer:update", kwargs={"pk": self.instance.pk})

    def test_contains_subject(self):
        self.login()
        resp = self.client.get(self.url)
        self.assertContains(resp, self.instance.subject)


class AdviceCreateTestCase(PermissionMixin, TemplateUsedMixin, TestCase):
    template_name = "advicer/advice_form.html"
    url = reverse_lazy("advicer:create")

    def setUp(self):
        super(AdviceCreateTestCase, self).setUp()
        self.user = StaffFactory(username="john")
        self.issue = IssueFactory()

    def test_keep_issues(self):
        self.login()
        resp = self.client.post(
            self.url,
            data={
                "issues": [self.issue.pk],
                "advicer": self.user.pk,
                "grant_on": datetime.datetime.now(),
                "attachment_set-INITIAL_FORMS": "0",
                "attachment_set-MAX_NUM_FORMS": "1000",
                "attachment_set-MIN_NUM_FORMS": "0",
                "attachment_set-TOTAL_FORMS": "3",
            },
        )
        self.assertEqual(resp.status_code, 302)
        advice = Advice.objects.last()
        self.assertTrue(advice.issues.filter(pk=self.issue.pk).exists())


class AdviceDeleteTestCase(InstanceMixin, PermissionMixin, TemplateUsedMixin, TestCase):
    template_name = "advicer/advice_confirm_delete.html"

    def setUp(self):
        super(AdviceDeleteTestCase, self).setUp()
        self.instance = AdviceFactory(advicer=self.user)
        self.url = reverse("advicer:delete", kwargs={"pk": self.instance.pk})

    def test_field_update(self):
        self.login()
        self.assertTrue(self.instance.visible)
        self.client.post(self.url)  # Perform action
        self.assertFalse(Advice.objects.get(pk=self.instance.pk).visible)

    def test_object_delete(self):
        self.login()
        self.client.post(self.url)
        self.assertFalse(Advice.objects.visible().filter(pk=self.instance.pk).exists())


class AdviceDetailTestCase(InstanceMixin, PermissionMixin, TemplateUsedMixin, TestCase):
    template_name = "advicer/advice_detail.html"

    def setUp(self):
        super(AdviceDetailTestCase, self).setUp()
        self.url = reverse("advicer:detail", kwargs={"pk": self.instance.pk})

    def test_linebreaks_in_comment(self):
        obj = AdviceFactory(created_by=self.user, comment="Lorem\nipsum")
        self.login()
        resp = self.client.get(obj.get_absolute_url())
        self.assertContains(resp, "Lorem<br>ipsum")


class AdviceQuerySetTestCase(TestCase):
    def test_for_user(self):
        self.assertFalse(
            Advice.objects.for_user(UserFactory())
            .filter(pk=AdviceFactory().pk)
            .exists()
        )
        # has perm
        user = UserFactory()
        assign_perm("advicer.can_view_all_advices", user)
        self.assertTrue(
            Advice.objects.for_user(user).filter(pk=AdviceFactory().pk).exists()
        )
        # advicer
        user = UserFactory()
        self.assertTrue(
            Advice.objects.for_user(user)
            .filter(pk=AdviceFactory(advicer=user).pk)
            .exists()
        )
        # created_by
        self.assertTrue(
            Advice.objects.for_user(user)
            .filter(pk=AdviceFactory(created_by=user).pk)
            .exists()
        )

    def test_visible(self):
        self.assertTrue(
            Advice.objects.visible().filter(pk=AdviceFactory(visible=True).pk).exists()
        )
        self.assertFalse(
            Advice.objects.visible().filter(pk=AdviceFactory(visible=False).pk).exists()
        )


class AdviceAdminTestCase(AdminTestCaseMixin, TestCase):
    user_factory_cls = UserFactory
    factory_cls = AdviceFactory
    model = Advice
