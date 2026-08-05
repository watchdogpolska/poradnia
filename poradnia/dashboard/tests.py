import datetime

from django.urls import reverse
from django.utils import timezone
from test_plus.test import TestCase

from poradnia.advicer.factories import (
    AdviceFactory,
    AreaFactory,
    InstitutionKindFactory,
    IssueFactory,
    PersonKindFactory,
)
from poradnia.cases.factories import CaseFactory
from poradnia.events.factories import EventFactory
from poradnia.judgements.factories import (
    CourtCaseFactory,
    CourtFactory,
    CourtSessionFactory,
)
from poradnia.letters.factories import AttachmentFactory, LetterFactory
from poradnia.users.factories import StaffFactory, UserFactory

from . import reports


def set_created_on(obj, date_str, field="created_on"):
    naive = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    aware = timezone.make_aware(naive)
    type(obj).objects.filter(pk=obj.pk).update(**{field: aware})
    obj.refresh_from_db()
    return obj


class UsersReportTestCase(TestCase):
    def test_bucketing_and_rollup(self):
        client_a = UserFactory()
        client_b = UserFactory()
        client_c = UserFactory()

        for _i in range(2):
            set_created_on(CaseFactory(client=client_a), "2024-01-15")
        for _i in range(7):
            set_created_on(CaseFactory(client=client_b), "2024-01-20")
        for _i in range(3):
            set_created_on(CaseFactory(client=client_c), "2024-02-05")
        for _i in range(4):
            set_created_on(CaseFactory(client=client_a), "2024-02-10")
        # Out of year - must be excluded.
        set_created_on(CaseFactory(client=client_a), "2023-01-15")

        report = reports.users_report(2024)
        rows = {row["month"]: row for row in report["rows"]}

        jan = rows["2024-01"]
        self.assertEqual(jan["users_with_new_case"], 2)
        self.assertEqual(jan["cases_le_5"], 1)
        self.assertEqual(jan["cases_6_10"], 1)

        feb = rows["2024-02"]
        self.assertEqual(feb["users_with_new_case"], 2)
        self.assertEqual(feb["cases_le_5"], 2)

        total = rows[str(reports.TOTAL_LABEL)]
        self.assertTrue(total["pinned"])
        # ROLLUP semantics: sums (client, month) groups, not distinct clients.
        self.assertEqual(total["users_with_new_case"], 4)
        self.assertEqual(total["cases_le_5"], 3)
        self.assertEqual(total["cases_6_10"], 1)


class CasesReportTestCase(TestCase):
    def test_letter_count_buckets(self):
        set_created_on(CaseFactory(letter_count=2), "2024-03-01")
        set_created_on(CaseFactory(letter_count=8), "2024-03-05")
        set_created_on(CaseFactory(letter_count=120), "2024-04-01")
        set_created_on(CaseFactory(letter_count=1), "2023-03-01")

        report = reports.cases_report(2024)
        rows = {row["month"]: row for row in report["rows"]}

        march = rows["2024-03"]
        self.assertEqual(march["cases_created"], 2)
        self.assertEqual(march["b_le5"], 1)
        self.assertEqual(march["b_6_10"], 1)

        april = rows["2024-04"]
        self.assertEqual(april["b_100p"], 1)

        total = rows[str(reports.TOTAL_LABEL)]
        self.assertTrue(total["pinned"])
        self.assertEqual(total["cases_created"], 3)
        self.assertEqual(total["b_100p"], 1)


class StaffLettersReportTestCase(TestCase):
    def test_staff_letters_and_attachments(self):
        staff_letter = LetterFactory(created_by_is_staff=True)
        set_created_on(staff_letter, "2024-05-10")
        AttachmentFactory(letter=staff_letter)
        AttachmentFactory(letter=staff_letter)

        other_staff_letter = LetterFactory(created_by_is_staff=True)
        set_created_on(other_staff_letter, "2024-05-11")

        client_letter = LetterFactory(created_by_is_staff=False)
        set_created_on(client_letter, "2024-05-12")

        report = reports.staff_letters_report(2024)
        rows = {row["month"]: row for row in report["rows"]}

        may = rows["2024-05"]
        self.assertEqual(may["letters_by_staff"], 2)
        self.assertEqual(may["attachments_by_staff"], 2)

        total = rows[str(reports.TOTAL_LABEL)]
        self.assertTrue(total["pinned"])
        self.assertEqual(total["letters_by_staff"], 2)
        self.assertEqual(total["attachments_by_staff"], 2)


class IssuesReportTestCase(TestCase):
    def test_per_issue_and_any_total(self):
        case_with_issue = CaseFactory()
        set_created_on(case_with_issue, "2024-06-01")
        case_without_issue = CaseFactory()
        set_created_on(case_without_issue, "2024-06-02")
        case_other_year = CaseFactory()
        set_created_on(case_other_year, "2023-06-01")

        issue = IssueFactory()
        advice = AdviceFactory(case=case_with_issue)
        advice.issues.add(issue)
        AdviceFactory(case=case_without_issue)
        other_advice = AdviceFactory(case=case_other_year)
        other_advice.issues.add(issue)

        report = reports.issues_report(2024)
        rows = {row["issue_name"]: row for row in report["rows"]}

        self.assertEqual(rows[issue.name]["cases_assigned"], 1)
        self.assertEqual(rows[issue.name]["cases_missing"], 1)

        any_total = rows[str(reports.ANY_TOTAL_LABEL)]
        self.assertTrue(any_total["pinned"])
        self.assertEqual(any_total["cases_assigned"], 1)
        self.assertEqual(any_total["cases_missing"], 1)


class InstitutionKindReportTestCase(TestCase):
    def test_per_kind_and_any_total(self):
        case_with_kind = CaseFactory()
        set_created_on(case_with_kind, "2024-07-01")
        case_without_kind = CaseFactory()
        set_created_on(case_without_kind, "2024-07-02")

        kind = InstitutionKindFactory()
        AdviceFactory(case=case_with_kind, institution_kind=kind)
        AdviceFactory(case=case_without_kind)

        report = reports.institution_kind_report(2024)
        rows = {row["kind_name"]: row for row in report["rows"]}

        self.assertEqual(rows[kind.name]["cases_assigned"], 1)
        self.assertEqual(rows[kind.name]["cases_missing"], 1)

        any_total = rows[str(reports.ANY_TOTAL_LABEL)]
        self.assertTrue(any_total["pinned"])
        self.assertEqual(any_total["cases_assigned"], 1)


class AreasAndPersonKindSmokeTestCase(TestCase):
    """Both share the exact _m2m_case_breakdown / _fk_case_breakdown helpers
    already covered in detail by IssuesReportTestCase / InstitutionKindReportTestCase
    - just check they execute and produce the trailing ANY/TOTAL row."""

    def test_areas_report_shape(self):
        case = CaseFactory()
        set_created_on(case, "2024-08-01")
        area = AreaFactory()
        advice = AdviceFactory(case=case)
        advice.area.add(area)

        report = reports.areas_report(2024)
        self.assertEqual(report["rows"][-1]["area_name"], str(reports.ANY_TOTAL_LABEL))
        self.assertTrue(report["rows"][-1]["pinned"])

    def test_person_kind_report_shape(self):
        case = CaseFactory()
        set_created_on(case, "2024-08-01")
        kind = PersonKindFactory()
        AdviceFactory(case=case, person_kind=kind)

        report = reports.person_kind_report(2024)
        self.assertEqual(report["rows"][-1]["kind_name"], str(reports.ANY_TOTAL_LABEL))
        self.assertTrue(report["rows"][-1]["pinned"])


class CourtSessionsReportTestCase(TestCase):
    def test_pivot_by_year(self):
        session_2023 = CourtSessionFactory(parser_key="wsa")
        set_created_on(session_2023, "2023-01-01", "created")
        session_2024_a = CourtSessionFactory(parser_key="wsa")
        set_created_on(session_2024_a, "2024-01-01", "created")
        session_2024_b = CourtSessionFactory(parser_key="nsa")
        set_created_on(session_2024_b, "2024-06-01", "created")

        report = reports.courtsessions_report()
        column_keys = {col["key"] for col in report["columns"]}
        self.assertIn("y_2023", column_keys)
        self.assertIn("y_2024", column_keys)

        rows = {row["parser_key"]: row for row in report["rows"]}
        self.assertEqual(rows["wsa"]["y_2023"], 1)
        self.assertEqual(rows["wsa"]["y_2024"], 1)
        self.assertEqual(rows["nsa"]["y_2024"], 1)

        total = rows[str(reports.TOTAL_LABEL)]
        self.assertTrue(total["pinned"])
        self.assertEqual(total["total"], 3)


class CourtCaseReportTestCase(TestCase):
    def test_grouped_by_court_with_none(self):
        court = CourtFactory(name="Sad Rejonowy")
        CourtCaseFactory(court=court)
        CourtCaseFactory(court=court)
        CourtCaseFactory(court=None)

        report = reports.courtcase_report()
        rows = {row["court_name"]: row for row in report["rows"]}

        self.assertEqual(rows["Sad Rejonowy"]["count"], 2)
        self.assertEqual(rows[str(reports.NONE_LABEL)]["count"], 1)

        total = rows[str(reports.TOTAL_LABEL)]
        self.assertTrue(total["pinned"])
        self.assertEqual(total["count"], 3)


class SummaryReportTestCase(TestCase):
    def test_yearly_metrics(self):
        client_a = UserFactory()
        case_2024 = CaseFactory(client=client_a)
        set_created_on(case_2024, "2024-03-01")
        case_2025 = CaseFactory(client=client_a)
        set_created_on(case_2025, "2025-01-10")

        staff_letter = LetterFactory(created_by_is_staff=True)
        set_created_on(staff_letter, "2024-05-01")
        AttachmentFactory(letter=staff_letter)

        court_case = CourtCaseFactory()
        set_created_on(court_case.record_general.get(), "2024-06-01")

        session = CourtSessionFactory()
        set_created_on(session, "2024-07-01", "created")

        event = EventFactory()
        set_created_on(event, "2024-08-01")

        report = reports.summary_report()
        rows = {row["metric"]: row for row in report["rows"]}

        self.assertEqual(rows[str(reports.NEW_CASES_LABEL)]["y_2024"], 1)
        self.assertEqual(rows[str(reports.NEW_CASES_LABEL)]["y_2025"], 1)
        self.assertEqual(rows[str(reports.NEW_USERS_WITH_CASES_LABEL)]["y_2024"], 1)
        self.assertEqual(rows[str(reports.STAFF_LETTERS_LABEL)]["y_2024"], 1)
        self.assertEqual(rows[str(reports.STAFF_ATTACHMENTS_LABEL)]["y_2024"], 1)
        self.assertEqual(rows[str(reports.COURT_CASES_LABEL)]["y_2024"], 1)
        self.assertEqual(rows[str(reports.COURT_SESSIONS_LABEL)]["y_2024"], 1)
        self.assertEqual(rows[str(reports.EVENTS_LABEL)]["y_2024"], 1)


class DashboardViewsTestCase(TestCase):
    def setUp(self):
        self.staff = StaffFactory()
        self.current_year = timezone.now().year

    def login_staff(self):
        self.client.login(username=self.staff.username, password="pass")

    def test_anonymous_denied(self):
        for url_name in ("index", "cases_tab", "advices_tab", "judgements_tab"):
            resp = self.client.get(reverse(f"dashboard:{url_name}"))
            self.assertEqual(resp.status_code, 403, url_name)

    def test_normal_user_denied(self):
        user = UserFactory()
        self.client.login(username=user.username, password="pass")
        resp = self.client.get(reverse("dashboard:index"))
        self.assertEqual(resp.status_code, 403)

    def test_index_default_year_and_summary_report(self):
        self.login_staff()
        resp = self.client.get(reverse("dashboard:index"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["current_year"], self.current_year)
        self.assertEqual(resp.context["years"][0], self.current_year)
        self.assertEqual(resp.context["years"][-1], 2018)

        summary_report = resp.context["summary_report"]
        self.assertEqual(len(summary_report["rows"]), 7)
        self.assertEqual(summary_report["columns"][-1]["key"], f"y_{self.current_year}")

    def test_cases_tab_year_param(self):
        self.login_staff()
        case = CaseFactory(letter_count=1)
        set_created_on(case, "2019-01-15")

        resp = self.client.get(reverse("dashboard:cases_tab"), {"year": 2019})
        self.assertEqual(resp.status_code, 200)
        cases_report = resp.context["cases_reports"][1]
        rows = {row["month"]: row for row in cases_report["rows"]}
        self.assertEqual(rows["2019-01"]["cases_created"], 1)

    def test_cases_tab_year_out_of_range_falls_back_to_current(self):
        self.login_staff()
        resp = self.client.get(reverse("dashboard:cases_tab"), {"year": 1999})
        self.assertEqual(resp.status_code, 200)

    def test_advices_tab_returns_four_reports(self):
        self.login_staff()
        resp = self.client.get(reverse("dashboard:advices_tab"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["advices_reports"]), 4)

    def test_judgements_tab_returns_two_reports(self):
        self.login_staff()
        resp = self.client.get(reverse("dashboard:judgements_tab"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["judgements_reports"]), 2)
