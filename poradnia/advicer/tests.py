import datetime
import json
import re

from atom.mixins import AdminTestCaseMixin
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import escape
from guardian.shortcuts import assign_perm
from test_plus.test import TestCase

from poradnia.advicer.models import Advice, Area, Issue
from poradnia.ai_assistant.models import N8nCaseTagsRequest
from poradnia.users.factories import StaffFactory, UserFactory

from .factories import (
    AdviceFactory,
    AreaFactory,
    InstitutionKindFactory,
    IssueFactory,
    PersonKindFactory,
)


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

    def test_show_comment_in_list(self):
        self.login()
        obj = AdviceFactory(advicer=self.user)
        resp = self.client.get(self.url)
        self.assertContains(resp, obj.comment)


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

    def test_no_thumbs_without_tags_request(self):
        self.login()
        resp = self.client.get(self.url)
        self.assertNotContains(resp, "fa-thumbs-up")
        self.assertNotContains(resp, "fa-thumbs-down")

    def test_both_thumbs_grey_when_unreviewed(self):
        tags_request = N8nCaseTagsRequest.objects.create(
            request_id="thumb-req-1", environment="TEST", question="q"
        )
        self.instance.ai_tags_request = tags_request
        self.instance.save()
        self.login()
        resp = self.client.get(self.url)
        self.assertContains(resp, "fa-thumbs-up")
        self.assertContains(resp, "fa-thumbs-down")
        self.assertNotContains(resp, "ai-thumb-up ai-thumb-active")
        self.assertNotContains(resp, "ai-thumb-down ai-thumb-active")

    def test_thumb_up_active_when_accepted(self):
        tags_request = N8nCaseTagsRequest.objects.create(
            request_id="thumb-req-2",
            environment="TEST",
            question="q",
            accepted_by=self.user,
            accepted_at=timezone.now(),
        )
        self.instance.ai_tags_request = tags_request
        self.instance.save()
        self.login()
        resp = self.client.get(self.url)
        self.assertContains(resp, "fa-thumbs-up")
        self.assertNotContains(resp, "fa-thumbs-down")

    def test_thumb_down_active_and_muted_when_rejected(self):
        tags_request = N8nCaseTagsRequest.objects.create(
            request_id="thumb-req-3",
            environment="TEST",
            question="q",
            rejected_by=self.user,
            rejected_at=timezone.now(),
            rejection_reason="Not relevant",
        )
        self.instance.ai_tags_request = tags_request
        self.instance.ai_assistant_tags = {"subject": "AI subject"}
        self.instance.save()
        self.login()
        resp = self.client.get(self.url)
        self.assertNotContains(resp, "fa-thumbs-up")
        self.assertContains(resp, "fa-thumbs-down")
        self.assertContains(resp, "ai-suggestion-rejected")
        self.assertContains(resp, "Not relevant")


class AdviceAiTagsAcceptViewTestCase(InstanceMixin, PermissionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.issue = IssueFactory()
        self.area = AreaFactory()
        self.person_kind = PersonKindFactory()
        self.institution_kind = InstitutionKindFactory()
        self.instance.issues.add(IssueFactory())
        self.instance.area.add(AreaFactory())
        self.tags_request = N8nCaseTagsRequest.objects.create(
            request_id="accept-req-1", environment="TEST", question="q"
        )
        self.instance.ai_tags_request = self.tags_request
        self.instance.ai_assistant_tags = {
            "subject": "AI subject",
            "summary": "AI summary",
            "person_kind": self.person_kind.pk,
            "institution_kind": self.institution_kind.pk,
            "issues": [self.issue.pk],
            "area": [self.area.pk],
            "comment": "AI comment",
        }
        self.instance.save()
        self.url = reverse("advicer:ai_tags_accept", kwargs={"pk": self.instance.pk})

    def test_contains_subject(self):
        # This is a POST-only action endpoint, unlike the GET-based detail
        # view InstanceMixin's test_contains_subject assumes.
        self.login()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 405)

    def test_anonymous_denied(self):
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_normal_user_denied(self):
        self.login(username=UserFactory().username)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_applies_all_ai_fields_and_replaces_m2m(self):
        self.login()
        self.client.post(self.url)
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.subject, "AI subject")
        self.assertEqual(self.instance.summary, "AI summary")
        self.assertEqual(self.instance.person_kind_id, self.person_kind.pk)
        self.assertEqual(self.instance.institution_kind_id, self.institution_kind.pk)
        self.assertEqual(
            set(self.instance.issues.values_list("pk", flat=True)), {self.issue.pk}
        )
        self.assertEqual(
            set(self.instance.area.values_list("pk", flat=True)), {self.area.pk}
        )

    def test_does_not_override_comment(self):
        original_comment = self.instance.comment
        self.login()
        self.client.post(self.url)
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.comment, original_comment)
        self.assertNotEqual(self.instance.comment, "AI comment")

    def test_sets_modified_by(self):
        self.login()
        self.client.post(self.url)
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.modified_by, self.user)

    def test_marks_request_accepted(self):
        self.login()
        self.client.post(self.url)
        self.tags_request.refresh_from_db()
        self.assertEqual(self.tags_request.accepted_by, self.user)
        self.assertIsNotNone(self.tags_request.accepted_at)
        self.assertIsNone(self.tags_request.rejected_at)

    def test_logs_change_entry(self):
        self.login()
        self.client.post(self.url)
        entry = LogEntry.objects.get(
            content_type=ContentType.objects.get_for_model(Advice),
            object_id=self.instance.pk,
        )
        self.assertEqual(entry.action_flag, CHANGE)

    def test_noop_when_no_tags_request(self):
        self.instance.ai_tags_request = None
        self.instance.save()
        original_subject = self.instance.subject
        self.login()
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.subject, original_subject)


class AdviceAiTagsRejectViewTestCase(InstanceMixin, PermissionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.tags_request = N8nCaseTagsRequest.objects.create(
            request_id="reject-req-1", environment="TEST", question="q"
        )
        self.instance.ai_tags_request = self.tags_request
        self.instance.ai_assistant_tags = {"subject": "AI subject"}
        self.instance.save()
        self.url = reverse("advicer:ai_tags_reject", kwargs={"pk": self.instance.pk})

    def test_contains_subject(self):
        # This is a POST-only action endpoint, unlike the GET-based detail
        # view InstanceMixin's test_contains_subject assumes.
        self.login()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 405)

    def test_anonymous_denied(self):
        resp = self.client.post(self.url, data={"rejection_reason": "no"})
        self.assertEqual(resp.status_code, 403)

    def test_normal_user_denied(self):
        self.login(username=UserFactory().username)
        resp = self.client.post(self.url, data={"rejection_reason": "no"})
        self.assertEqual(resp.status_code, 403)

    def test_blank_reason_returns_400(self):
        self.login()
        resp = self.client.post(self.url, data={"rejection_reason": "   "})
        self.assertEqual(resp.status_code, 400)
        self.tags_request.refresh_from_db()
        self.assertIsNone(self.tags_request.rejected_at)

    def test_missing_reason_returns_400(self):
        self.login()
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 400)

    def test_marks_request_rejected(self):
        self.login()
        self.client.post(self.url, data={"rejection_reason": "Not relevant"})
        self.tags_request.refresh_from_db()
        self.assertEqual(self.tags_request.rejected_by, self.user)
        self.assertIsNotNone(self.tags_request.rejected_at)
        self.assertEqual(self.tags_request.rejection_reason, "Not relevant")
        self.assertIsNone(self.tags_request.accepted_at)

    def test_does_not_change_advice_fields(self):
        original_subject = self.instance.subject
        self.login()
        self.client.post(self.url, data={"rejection_reason": "Not relevant"})
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.subject, original_subject)

    def test_noop_when_no_tags_request(self):
        self.instance.ai_tags_request = None
        self.instance.save()
        self.login()
        resp = self.client.post(self.url, data={"rejection_reason": "Not relevant"})
        self.assertEqual(resp.status_code, 200)


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


class AdviceAiReviewFlagsQuerySetTestCase(TestCase):
    def setUp(self):
        self.advice = AdviceFactory()

    def _flags(self):
        return Advice.objects.with_ai_review_flags().get(pk=self.advice.pk)

    def test_no_ai_data_all_flags_false(self):
        obj = self._flags()
        self.assertFalse(obj.has_ai_tag_suggestion)
        self.assertFalse(obj.has_ai_tag_suggestion_to_review)

    def test_has_ai_tag_suggestion_true_when_linked(self):
        tags_request = N8nCaseTagsRequest.objects.create(
            request_id="tags-1", environment="TEST", question="q"
        )
        self.advice.ai_tags_request = tags_request
        self.advice.save(update_fields=["ai_tags_request"])
        obj = self._flags()
        self.assertTrue(obj.has_ai_tag_suggestion)
        self.assertTrue(obj.has_ai_tag_suggestion_to_review)

    def test_has_ai_tag_suggestion_to_review_false_once_accepted(self):
        tags_request = N8nCaseTagsRequest.objects.create(
            request_id="tags-2",
            environment="TEST",
            question="q",
            accepted_at=timezone.now(),
        )
        self.advice.ai_tags_request = tags_request
        self.advice.save(update_fields=["ai_tags_request"])
        obj = self._flags()
        self.assertTrue(obj.has_ai_tag_suggestion)
        self.assertFalse(obj.has_ai_tag_suggestion_to_review)

    def test_has_ai_tag_suggestion_to_review_false_once_rejected(self):
        tags_request = N8nCaseTagsRequest.objects.create(
            request_id="tags-3",
            environment="TEST",
            question="q",
            rejected_at=timezone.now(),
            rejection_reason="not relevant",
        )
        self.advice.ai_tags_request = tags_request
        self.advice.save(update_fields=["ai_tags_request"])
        obj = self._flags()
        self.assertTrue(obj.has_ai_tag_suggestion)
        self.assertFalse(obj.has_ai_tag_suggestion_to_review)


class AdviceAdminTestCase(AdminTestCaseMixin, TestCase):
    user_factory_cls = UserFactory
    factory_cls = AdviceFactory
    model = Advice


class IssueActiveAsJsonTestCase(TestCase):
    def test_excludes_inactive(self):
        inactive = IssueFactory(active=False)
        data = json.loads(Issue.active_as_json())
        self.assertNotIn(inactive.pk, [item["id"] for item in data])

    def test_includes_active(self):
        issue = IssueFactory(active=True)
        data = json.loads(Issue.active_as_json())
        self.assertIn(issue.pk, [item["id"] for item in data])

    def test_fields(self):
        issue = IssueFactory(active=True)
        data = json.loads(Issue.active_as_json())
        item = next(d for d in data if d["id"] == issue.pk)
        self.assertEqual(
            set(item.keys()),
            {"id", "name", "tag_helper", "is_dip", "is_local_government"},
        )


class AreaActiveAsJsonTestCase(TestCase):
    def test_excludes_inactive(self):
        inactive = AreaFactory(active=False)
        data = json.loads(Area.active_as_json())
        self.assertNotIn(inactive.pk, [item["id"] for item in data])

    def test_includes_active(self):
        area = AreaFactory(active=True)
        data = json.loads(Area.active_as_json())
        self.assertIn(area.pk, [item["id"] for item in data])

    def test_fields(self):
        area = AreaFactory(active=True)
        data = json.loads(Area.active_as_json())
        item = next(d for d in data if d["id"] == area.pk)
        self.assertEqual(
            set(item.keys()),
            {"id", "name", "tag_helper", "is_dip", "is_local_government"},
        )


def autocomplete_results(response_text):
    """
    Parse an autocomplete-light HTML fragment response into (id, label) pairs.

    Note, that this function drops a lot of information. For each autocomplete
    endpoint, there should exists a test that validates the whole fragment and
    does not utilize this function.
    """
    return [
        (int(value), label)
        for value, label in re.findall(
            r'<div data-value="([^"]*)">(.*?)</div>', response_text
        )
    ]


def autocomplete_ids(response_text):
    return [pk for pk, _label in autocomplete_results(response_text)]


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

        results = autocomplete_results(response.text)
        self.assertEqual(len(results), 1)

        result_id, result_label = results[0]
        self.assertEqual(result_id, issue.id)
        self.assertEqual(result_label, escape(issue.name))

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
            set(autocomplete_ids(response_common.text)),
            {issue_1.id, issue_2.id, issue_3.id},
        )

        # Search for a unique fragment. Single match expected.
        response_unique = self.client.get(self.url, {"q": "2"})
        self.assertEqual(response_unique.status_code, 200)
        self.assertEqual(autocomplete_ids(response_unique.text), [issue_2.id])

        # Search for a non-existent fragment. No matches expected.
        response_nonexistent = self.client.get(self.url, {"q": "some-unknown-id"})
        self.assertEqual(response_nonexistent.status_code, 200)
        self.assertEqual(autocomplete_ids(response_nonexistent.text), [])


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

        results = autocomplete_results(response.text)
        self.assertEqual(len(results), 1)

        result_id, result_label = results[0]
        self.assertEqual(result_id, area.id)
        self.assertEqual(result_label, escape(area.name))

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
            set(autocomplete_ids(response_common.text)),
            {area_1.id, area_2.id, area_3.id},
        )

        # Search for a unique fragment. Single match expected.
        response_unique = self.client.get(self.url, {"q": "2"})
        self.assertEqual(response_unique.status_code, 200)
        self.assertEqual(autocomplete_ids(response_unique.text), [area_2.id])

        # Search for a non-existent fragment. No matches expected.
        response_nonexistent = self.client.get(self.url, {"q": "some-unknown-id"})
        self.assertEqual(response_nonexistent.status_code, 200)
        self.assertEqual(autocomplete_ids(response_nonexistent.text), [])
