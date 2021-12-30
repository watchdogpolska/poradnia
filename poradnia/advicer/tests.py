import datetime

from atom.mixins import AdminTestCaseMixin
from django.test import RequestFactory
from django.urls import reverse, reverse_lazy
from guardian.shortcuts import assign_perm
from test_plus.test import TestCase

from poradnia.advicer.models import Advice
from poradnia.users.factories import StaffFactory, UserFactory

from .factories import AdviceFactory, AreaFactory, IssueFactory


class PermissionMixin:
    def setUp(self):
        super().setUp()
        self.user = StaffFactory()

    def login(self, username=None):
        self.client.login(username=username or self.user.username, password="pass")

    def test_anonymous_denied(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_normal_user_denied(self):
        self.login(username=UserFactory().username)
        self.test_anonymous_denied()


class TemplateUsedMixin:
    def test_template_used(self):
        self.login()
        resp = self.client.get(self.url)
        self.assertTemplateUsed(resp, self.template_name)


class InstanceMixin:
    def setUp(self):
        super().setUp()
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
        super().setUp()
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
        super().setUp()
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
        super().setUp()
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
        super().setUp()
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


def autocomplete_ids(autocomplete_response):
    """
    Autocomplete response contains more data than just the matching ids.
    Dig ids from the object.

    Note, that this function drops a lot of information. For each autocomplete
    endpoint, there should exists a test that validates the whole object and
    does not utilize this function.
    """
    results = autocomplete_response["results"]
    return [int(result["id"]) for result in results]


class IssueAutocompleteViewTestCase(TestCase):
    url = reverse_lazy("advicer:issue-autocomplete")

    def test_regular_user_cannot_access(self):
        user = UserFactory()
        IssueFactory(name="issue-1")

        self.client.force_login(user)

        response = self.client.get(self.url, {"q": "issue"})
        self.assertNotEqual(response.status_code, 200)

    def test_response_format(self):
        """
        Validate that the response contains all data that we want to render in
        the UI.
        """
        user = StaffFactory()
        issue = IssueFactory(name="issue")

        self.client.force_login(user)

        response = self.client.get(self.url, {"q": "issue"})
        self.assertEqual(response.status_code, 200)

        results = response.json()["results"]
        self.assertEqual(len(results), 1)

        result = results[0]
        self.assertEqual(result["id"], str(issue.id))
        self.assertEqual(result["text"], issue.name)

    def test_search_results(self):
        """
        Validate the endpoint's response to various queries.
        """
        user = StaffFactory()

        # Create a few issues to search for.
        issue_1 = IssueFactory(name="issue-1")
        issue_2 = IssueFactory(name="issue-2")
        issue_3 = IssueFactory(name="issue-3")

        self.client.force_login(user)

        # Search for a common fragment. Multiple matches expected.
        response_common = self.client.get(self.url, {"q": "issue"})
        self.assertEqual(response_common.status_code, 200)
        # The order is not validated here.
        self.assertEqual(
            set(autocomplete_ids(response_common.json())),
            {issue_1.id, issue_2.id, issue_3.id},
        )

        # Search for a unique fragment. Single match expected.
        response_unique = self.client.get(self.url, {"q": "2"})
        self.assertEqual(response_unique.status_code, 200)
        self.assertEqual(autocomplete_ids(response_unique.json()), [issue_2.id])

        # Search for a non-existent fragment. No matches expected.
        response_nonexistent = self.client.get(self.url, {"q": "some-unknown-id"})
        self.assertEqual(response_nonexistent.status_code, 200)
        self.assertEqual(autocomplete_ids(response_nonexistent.json()), [])


class AreaAutocompleteViewTestCase(TestCase):
    url = reverse_lazy("advicer:area-autocomplete")

    def test_regular_user_cannot_access(self):
        user = UserFactory()
        AreaFactory(name="area-1")

        self.client.force_login(user)

        response = self.client.get(self.url, {"q": "area"})
        self.assertNotEqual(response.status_code, 200)

    def test_response_format(self):
        """
        Validate that the response contains all data that we want to render in
        the UI.
        """
        user = StaffFactory()
        area = AreaFactory(name="area")

        self.client.force_login(user)

        response = self.client.get(self.url, {"q": "area"})
        self.assertEqual(response.status_code, 200)

        results = response.json()["results"]
        self.assertEqual(len(results), 1)

        result = results[0]
        self.assertEqual(result["id"], str(area.id))
        self.assertEqual(result["text"], area.name)

    def test_search_results(self):
        """
        Validate the endpoint's response to various queries.
        """
        user = StaffFactory()

        # Create a few areas to search for.
        area_1 = AreaFactory(name="area-1")
        area_2 = AreaFactory(name="area-2")
        area_3 = AreaFactory(name="area-3")

        self.client.force_login(user)

        # Search for a common fragment. Multiple matches expected.
        response_common = self.client.get(self.url, {"q": "area"})
        self.assertEqual(response_common.status_code, 200)
        # The order is not validated here.
        self.assertEqual(
            set(autocomplete_ids(response_common.json())),
            {area_1.id, area_2.id, area_3.id},
        )

        # Search for a unique fragment. Single match expected.
        response_unique = self.client.get(self.url, {"q": "2"})
        self.assertEqual(response_unique.status_code, 200)
        self.assertEqual(autocomplete_ids(response_unique.json()), [area_2.id])

        # Search for a non-existent fragment. No matches expected.
        response_nonexistent = self.client.get(self.url, {"q": "some-unknown-id"})
        self.assertEqual(response_nonexistent.status_code, 200)
        self.assertEqual(autocomplete_ids(response_nonexistent.json()), [])
