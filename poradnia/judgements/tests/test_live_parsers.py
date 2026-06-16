from django.test import SimpleTestCase, tag

from poradnia.judgements.registry import get_parser_keys, parser_registry


@tag("live")
class LiveParserTestCase(SimpleTestCase):
    """
    Tests parser compatibility against live court URLs.
    No database required — uses SimpleTestCase.
    Run weekly by the monitor_court_parsers celery task.
    """

    def test_all_parsers_reachable_and_parseable(self):
        for parser_key in get_parser_keys():
            with self.subTest(parser_key=parser_key):
                parser = parser_registry[parser_key]()
                rows = list(parser.get_session_rows())
                for row in rows[:3]:
                    self.assertTrue(row.signature, f"{parser_key}: empty signature")
                    self.assertIsNotNone(
                        row.datetime, f"{parser_key}: missing datetime"
                    )
                    self.assertTrue(row.description, f"{parser_key}: empty description")
