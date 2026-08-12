from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from guardian.shortcuts import assign_perm

from poradnia.ai_assistant.models import N8nArticlesSearchRequest
from poradnia.cases.factories import CaseFactory
from poradnia.letters.factories import LetterFactory
from poradnia.users.factories import StaffFactory


class AiReviewLetterMixin:
    def setUp(self):
        self.user = StaffFactory(username="john", password="pass")
        self.case = CaseFactory()
        self.letter = LetterFactory(
            case=self.case,
            genre="ai_message_staff",
            status="staff",
            created_by_is_staff=True,
        )
        self.search_request = N8nArticlesSearchRequest.objects.create(
            request_id="req-1",
            environment="TEST",
            question="q",
            case=self.case,
            letter=self.letter,
        )

    def _grant_view(self):
        assign_perm("can_view", self.user, self.case)

    def _grant_permission(self):
        self._grant_view()
        assign_perm("cases.can_change_case", self.user, self.case)


class LetterAiSearchAcceptViewTestCase(AiReviewLetterMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("letters:ai_search_accept", kwargs={"pk": self.letter.pk})

    def test_anonymous_user_is_redirected(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/konta/login/", response["Location"])

    def test_authenticated_user_without_permission_gets_403(self):
        self._grant_view()
        self.client.login(username="john", password="pass")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_request_is_not_allowed(self):
        self._grant_permission()
        self.client.login(username="john", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_marks_request_accepted(self):
        self._grant_permission()
        self.client.login(username="john", password="pass")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)

        self.search_request.refresh_from_db()
        self.assertEqual(self.search_request.accepted_by, self.user)
        self.assertIsNotNone(self.search_request.accepted_at)

    def test_noop_when_already_rejected(self):
        self.search_request.rejected_by = self.user
        self.search_request.rejected_at = timezone.now()
        self.search_request.rejection_reason = "bad answer"
        self.search_request.save()

        self._grant_permission()
        self.client.login(username="john", password="pass")
        self.client.post(self.url)

        self.search_request.refresh_from_db()
        self.assertIsNone(self.search_request.accepted_by)
        self.assertIsNone(self.search_request.accepted_at)
        self.assertEqual(self.search_request.rejection_reason, "bad answer")

    def test_noop_when_no_search_request_linked(self):
        self.search_request.letter = None
        self.search_request.save(update_fields=["letter"])

        self._grant_permission()
        self.client.login(username="john", password="pass")
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)


class LetterAiSearchRejectViewTestCase(AiReviewLetterMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("letters:ai_search_reject", kwargs={"pk": self.letter.pk})

    def test_anonymous_user_is_redirected(self):
        response = self.client.post(self.url, {"rejection_reason": "bad"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/konta/login/", response["Location"])

    def test_authenticated_user_without_permission_gets_403(self):
        self._grant_view()
        self.client.login(username="john", password="pass")
        response = self.client.post(self.url, {"rejection_reason": "bad"})
        self.assertEqual(response.status_code, 403)

    def test_get_request_is_not_allowed(self):
        self._grant_permission()
        self.client.login(username="john", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_requires_rejection_reason(self):
        self._grant_permission()
        self.client.login(username="john", password="pass")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)

        response = self.client.post(self.url, {"rejection_reason": "   "})
        self.assertEqual(response.status_code, 400)

        self.search_request.refresh_from_db()
        self.assertIsNone(self.search_request.rejected_at)

    def test_marks_request_rejected_with_reason(self):
        self._grant_permission()
        self.client.login(username="john", password="pass")
        response = self.client.post(self.url, {"rejection_reason": "Not relevant"})
        self.assertEqual(response.status_code, 200)

        self.search_request.refresh_from_db()
        self.assertEqual(self.search_request.rejected_by, self.user)
        self.assertIsNotNone(self.search_request.rejected_at)
        self.assertEqual(self.search_request.rejection_reason, "Not relevant")

    def test_noop_when_already_accepted(self):
        self.search_request.accepted_by = self.user
        self.search_request.accepted_at = self.search_request.created_at
        self.search_request.save()

        self._grant_permission()
        self.client.login(username="john", password="pass")
        self.client.post(self.url, {"rejection_reason": "Not relevant"})

        self.search_request.refresh_from_db()
        self.assertIsNone(self.search_request.rejected_by)
        self.assertIsNone(self.search_request.rejected_at)

    def test_noop_when_no_search_request_linked(self):
        self.search_request.letter = None
        self.search_request.save(update_fields=["letter"])

        self._grant_permission()
        self.client.login(username="john", password="pass")
        response = self.client.post(self.url, {"rejection_reason": "Not relevant"})

        self.assertEqual(response.status_code, 200)


class LetterAiFeedbackTemplateTestCase(TestCase):
    def setUp(self):
        self.user = StaffFactory(username="jane", password="pass")
        self.case = CaseFactory()
        assign_perm("can_view", self.user, self.case)
        assign_perm("cases.can_change_case", self.user, self.case)
        assign_perm("cases.can_change_all_record", self.user, self.case)
        self.client.login(username="jane", password="pass")

    def _make_ai_letter(self, request_id, **request_kwargs):
        letter = LetterFactory(
            case=self.case,
            genre="ai_message_staff",
            status="staff",
            created_by_is_staff=True,
        )
        sr = N8nArticlesSearchRequest.objects.create(
            request_id=request_id,
            environment="TEST",
            question="q",
            case=self.case,
            letter=letter,
            **request_kwargs,
        )
        return letter, sr

    def test_no_thumbs_for_non_ai_letter(self):
        LetterFactory(case=self.case, genre="mail", status="done")
        response = self.client.get(self.case.get_absolute_url())
        self.assertNotContains(response, "ai-thumb-up")
        self.assertNotContains(response, "ai-thumb-down")

    def test_no_thumbs_without_can_change_case(self):
        other_user = StaffFactory(username="observer", password="pass")
        assign_perm("can_view", other_user, self.case)
        self.client.login(username="observer", password="pass")
        self._make_ai_letter("req-view-only")

        response = self.client.get(self.case.get_absolute_url())
        self.assertNotContains(response, "ai-thumb-up")
        self.assertNotContains(response, "ai-thumb-down")

    def test_no_thumbs_when_unlinked(self):
        LetterFactory(
            case=self.case,
            genre="ai_message_staff",
            status="staff",
            created_by_is_staff=True,
        )
        response = self.client.get(self.case.get_absolute_url())
        self.assertNotContains(response, "ai-thumb-up")
        self.assertNotContains(response, "ai-thumb-down")

    def test_both_thumbs_shown_when_undecided(self):
        self._make_ai_letter("req-pending")
        response = self.client.get(self.case.get_absolute_url())
        # "ai-thumb-active"/"ai-suggestion-rejected" also appear in the page's
        # <style> block regardless of state, so check the button's own class
        # attribute rather than the whole response for this one.
        self.assertContains(response, "ai-thumb-up")
        self.assertContains(response, "ai-thumb-down")
        self.assertNotContains(response, "ai-thumb-up ai-thumb-active")

    def test_only_thumb_up_active_after_accept(self):
        self._make_ai_letter(
            "req-accepted", accepted_by=self.user, accepted_at=timezone.now()
        )
        response = self.client.get(self.case.get_absolute_url())
        content = response.content.decode()
        self.assertIn("ai-thumb-up", content)
        self.assertIn("ai-thumb-active", content)
        self.assertNotIn("ai-thumb-down", content)

    def test_only_thumb_down_active_after_reject(self):
        self._make_ai_letter(
            "req-rejected",
            rejected_by=self.user,
            rejected_at=timezone.now(),
            rejection_reason="Outdated info",
        )
        response = self.client.get(self.case.get_absolute_url())
        content = response.content.decode()
        self.assertIn("ai-thumb-down", content)
        self.assertIn("ai-thumb-active", content)
        self.assertIn("Outdated info", content)
        self.assertNotIn("ai-thumb-up", content)

    def test_two_ai_letters_do_not_cross_contaminate(self):
        letter_a, sr_a = self._make_ai_letter("req-a")
        letter_b, sr_b = self._make_ai_letter("req-b")

        self.client.post(
            reverse("letters:ai_search_accept", kwargs={"pk": letter_a.pk})
        )
        self.client.post(
            reverse("letters:ai_search_reject", kwargs={"pk": letter_b.pk}),
            {"rejection_reason": "Wrong articles"},
        )

        sr_a.refresh_from_db()
        sr_b.refresh_from_db()
        self.assertIsNotNone(sr_a.accepted_at)
        self.assertIsNone(sr_a.rejected_at)
        self.assertIsNone(sr_b.accepted_at)
        self.assertIsNotNone(sr_b.rejected_at)
        self.assertEqual(sr_b.rejection_reason, "Wrong articles")

        response = self.client.get(self.case.get_absolute_url())
        content = response.content.decode()
        self.assertIn(f"ai-feedback-{letter_a.pk}", content)
        self.assertIn(f"ai-feedback-{letter_b.pk}", content)

    def test_delete_link_hidden_for_pending_and_accepted_ai_letter(self):
        pending_letter, _ = self._make_ai_letter("req-del-pending")
        accepted_letter, _ = self._make_ai_letter(
            "req-del-accepted", accepted_by=self.user, accepted_at=timezone.now()
        )
        response = self.client.get(self.case.get_absolute_url())
        content = response.content.decode()
        self.assertNotIn(pending_letter.render_admin_delete_link(), content)
        self.assertNotIn(accepted_letter.render_admin_delete_link(), content)

    def test_delete_link_shown_for_rejected_ai_letter(self):
        rejected_letter, _ = self._make_ai_letter(
            "req-del-rejected",
            rejected_by=self.user,
            rejected_at=timezone.now(),
            rejection_reason="Bad",
        )
        response = self.client.get(self.case.get_absolute_url())
        self.assertContains(response, rejected_letter.render_admin_delete_link())

    def test_delete_link_unaffected_for_non_ai_letter(self):
        letter = LetterFactory(case=self.case, genre="mail", status="done")
        response = self.client.get(self.case.get_absolute_url())
        self.assertContains(response, letter.render_admin_delete_link())
