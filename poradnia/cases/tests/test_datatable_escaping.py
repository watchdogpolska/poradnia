"""DataTables inserts AJAX cell values as HTML, so every renderer that puts
user-supplied text into a cell must escape it."""

from django.test import RequestFactory, TestCase
from guardian.shortcuts import assign_perm

from poradnia.advicer.factories import AdviceFactory
from poradnia.cases.factories import CaseFactory
from poradnia.events.factories import EventFactory
from poradnia.letters.factories import LetterFactory
from poradnia.letters.views.cbv import LetterAjaxDatatableView
from poradnia.users.factories import UserFactory

PAYLOAD = '<img src=x onerror="alert(1)">'
ESCAPED = "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;"


class DatatableCellEscapingTestCase(TestCase):
    def assertEscaped(self, html):
        self.assertNotIn("<img", html)
        self.assertIn(ESCAPED, html)

    def test_case_link(self):
        self.assertEscaped(CaseFactory(name=PAYLOAD).render_case_link())

    def test_case_involved_staff(self):
        case = CaseFactory()
        assign_perm(
            "cases.can_view", UserFactory(is_staff=True, first_name=PAYLOAD), case
        )
        self.assertEscaped(case.render_involved_staff())

    def test_letter_link(self):
        self.assertEscaped(LetterFactory(name=PAYLOAD).render_letter_link())

    def test_letter_table_text(self):
        letter = LetterFactory(text=PAYLOAD)
        view = LetterAjaxDatatableView()
        view.request = RequestFactory().get("/")
        view.request.user = UserFactory(is_staff=True)
        row = {}
        view.customize_row(row, letter)
        self.assertEscaped(row["text"])

    def test_advice_link(self):
        self.assertEscaped(AdviceFactory(subject=PAYLOAD).render_advice_link())

    def test_event_link_escapes_but_keeps_line_breaks(self):
        html = EventFactory(text=PAYLOAD + "\nsecond").render_event_link
        self.assertEscaped(html)
        self.assertIn("<br>second", html)
