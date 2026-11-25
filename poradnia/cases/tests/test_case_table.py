from django.test import TestCase
from django.urls import reverse, reverse_lazy
from guardian.shortcuts import assign_perm

from poradnia.ai_assistant.models import N8nSimilarCasesRequest
from poradnia.cases.factories import CaseFactory
from poradnia.cases.models import Case
from poradnia.letters.factories import LetterFactory
from poradnia.users.factories import StaffFactory

BOOLEAN_FILTERS = (
    "handled",
    "has_tag",
    "has_deadline",
    "has_ai_articles",
    "has_ai_articles_to_review",
    "has_ai_similar_cases",
    "has_ai_similar_cases_to_review",
    "has_ai_tag_suggestion",
)


class CaseTableViewTestCase(TestCase):
    def test_renders_ai_similar_cases_filters(self):
        user = StaffFactory()
        self.client.login(username=user.username, password="pass")
        resp = self.client.get(reverse("cases:table"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "cases/case_table.html")
        for name in ("has_ai_similar_cases", "has_ai_similar_cases_to_review"):
            for choice in ("yes", "no"):
                self.assertContains(resp, f'name="check_{name}_{choice}"')
        self.assertContains(resp, "Ma podobne sprawy AI")
        self.assertContains(resp, "Podobne sprawy AI do oceny")


class CaseAjaxDatatableSimilarCasesFilterTestCase(TestCase):
    url = reverse_lazy("cases:case_table_ajax_data")

    def setUp(self):
        self.user = StaffFactory()
        assign_perm("cases.can_view", self.user)  # global: every case
        self.client.login(username=self.user.username, password="pass")
        self.without = CaseFactory()
        self.to_review = self._case_with_similar_cases()
        self.reviewed = self._case_with_similar_cases(accepted=True)

    def _case_with_similar_cases(self, accepted=False):
        case = CaseFactory()
        letter = LetterFactory(case=case, genre="ai_message_staff", status="staff")
        N8nSimilarCasesRequest.objects.create(
            request_id=f"sim-{case.pk}",
            environment="TEST",
            question="q",
            case=case,
            letter=letter,
            accepted_at=letter.created_on if accepted else None,
        )
        return case

    def _get_columns(self):
        resp = self.client.post(self.url, {"action": "initialize"})
        return resp.json()["columns"]

    def _get_case_pks(self, **overrides):
        data = {
            "draw": 1,
            "start": 0,
            "length": 200,
            "search[value]": "",
            "search[regex]": "false",
        }
        for status in Case.STATUS._identifier_map:
            data[f"status_{status}"] = 1
        for name in BOOLEAN_FILTERS:
            data[f"{name}_yes"] = 1
            data[f"{name}_no"] = 1
        data.update(overrides)
        for index, column in enumerate(self._get_columns()):
            data[f"columns[{index}][data]"] = column["name"]
            data[f"columns[{index}][name]"] = column["name"]
            data[f"columns[{index}][searchable]"] = "true"
            data[f"columns[{index}][orderable]"] = "true"
            data[f"columns[{index}][search][regex]"] = "false"
            data[f"columns[{index}][search][value]"] = ""
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        return {
            int(row["DT_RowId"].removeprefix("row-")) for row in resp.json()["data"]
        }

    def test_all_checked_returns_every_case(self):
        self.assertEqual(
            self._get_case_pks(),
            {self.without.pk, self.to_review.pk, self.reviewed.pk},
        )

    def test_has_ai_similar_cases_yes_only(self):
        self.assertEqual(
            self._get_case_pks(has_ai_similar_cases_no=0),
            {self.to_review.pk, self.reviewed.pk},
        )

    def test_has_ai_similar_cases_no_only(self):
        self.assertEqual(
            self._get_case_pks(has_ai_similar_cases_yes=0), {self.without.pk}
        )

    def test_ai_similar_cases_to_review_yes_only(self):
        self.assertEqual(
            self._get_case_pks(has_ai_similar_cases_to_review_no=0),
            {self.to_review.pk},
        )

    def test_ai_similar_cases_to_review_none_checked_returns_nothing(self):
        self.assertEqual(
            self._get_case_pks(
                has_ai_similar_cases_to_review_yes=0,
                has_ai_similar_cases_to_review_no=0,
            ),
            set(),
        )
