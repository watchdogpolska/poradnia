from django.test import TestCase
from django.core.management import call_command

from poradnia.judgements.factories import CourtFactory

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class RunCourtSessionParserTestCase(TestCase):
    def test_run_command_basic(self):
        court = CourtFactory(name="MyFooCourt")
        stdout = StringIO()
        call_command("run_court_session_parser", stdout=stdout)
        self.assertIn("MyFooCourt", stdout.getvalue())
