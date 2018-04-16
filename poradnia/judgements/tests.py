
import inspect
import os
from unittest.mock import Mock

from django.test import TestCase

from django.utils import six
from vcr import VCR

from poradnia.events.models import Event
from poradnia.judgements.factories import CourtFactory, CourtCaseFactory, SessionRowFactory, CourtSessionFactory
from poradnia.judgements.registry import get_parser_keys
from poradnia.judgements.utils import Manager
from poradnia.users.factories import UserFactory

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


def generator(f, suffix=None):
    if six.PY3:
        filename = "{}.{}".format(f.__self__.__class__.__name__, f.__name__)
    else:
        filename = "{}.{}".format(f.im_class.__name__, f.__name__)
    if suffix:
        filename = "{}.{}".format(suffix, filename)
    return os.path.join(os.path.dirname(inspect.getfile(f)),
                        'cassettes', filename)


my_vcr = VCR(func_path_generator=generator,
             decode_compressed_response=True,
             serializer='yaml',
             path_transformer=VCR.ensure_suffix('.yaml'))


class ParserTestCaseMixin(TestCase):
    @my_vcr.use_cassette()
    def test_return_valid_signaturerow(self):
        for parser_key in get_parser_keys():
            court = CourtFactory(parser_key=parser_key)
            with my_vcr.use_cassette(generator(f=self.test_return_valid_signaturerow,
                                               suffix=parser_key)):
                for i, session_row in enumerate(court.get_parser().get_session_rows()):
                    msg = "Failed for {} in {}".format(i, parser_key)
                    self.assertTrue(session_row.signature, msg=msg)
                    self.assertTrue(session_row.datetime, msg=msg)
                    self.assertTrue(session_row.description, msg=msg)
                    self.assertIn(session_row.signature, session_row.description, msg=msg)

    def test_required_parser(self):
        required_parsers = ['NSA',
                            'WSA_Bialystok', 'WSA_Bydgoszcz', 'WSA_Gdansk',
                            'WSA_Gliwice', 'WSA_Gorzow', 'WSA_Kielce',
                            'WSA_Krakow', 'WSA_Lodz', 'WSA_Lublin',
                            'WSA_Olsztyn', 'WSA_Opole', 'WSA_Poznan',
                            'WSA_Rzeszow', 'WSA_Szczecin', 'WSA_Warszawa',
                            # 'WSA_Wroclaw'  # missing
                            ]
        supported = set(get_parser_keys())
        for requirement in required_parsers:
            self.assertIn(requirement, supported, msg="Missing {}".format(requirement))


class ManagerTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.manager = Manager(bot=self.user, stdout=self.stdout, stderr=self.stderr)

    def test_create_new_event(self):
        courtcase = CourtCaseFactory()
        session_row = SessionRowFactory(signature=courtcase.signature)
        mock = Mock(get_session_rows=lambda: [session_row])
        self.manager.handle_court(courtcase.court, mock)
        event = Event.objects.get()
        self.assertEqual(event.time, session_row.datetime)
        self.assertEqual(event.text, session_row.description)

    def test_update_event_text_on_new_session_row_text(self):
        courtsession = CourtSessionFactory()
        courtcase = courtsession.courtcase
        old_event = courtsession.event
        session_row = SessionRowFactory(signature=courtcase.signature,
                                        datetime=old_event.time)
        mock = Mock(get_session_rows=lambda: [session_row])
        self.manager.handle_court(courtsession.courtcase.court, mock)
        self.assertEqual(Event.objects.count(), 1)
        old_event.refresh_from_db()
        self.assertEqual(old_event.time, session_row.datetime)
        self.assertEqual(old_event.text, session_row.description)
        self.assertEqual(old_event.modified_by, self.user)

    def test_skip_update_event_if_sessio_row_match(self):
        courtsession = CourtSessionFactory()
        courtcase = courtsession.courtcase
        old_event = courtsession.event
        session_row = SessionRowFactory(signature=courtcase.signature,
                                        datetime=old_event.time,
                                        description=old_event.text)
        mock = Mock(get_session_rows=lambda: [session_row])
        self.manager.handle_court(courtsession.courtcase.court, mock)
        self.assertEqual(Event.objects.count(), 1)
        old_event.refresh_from_db()
        self.assertEqual(old_event.time, session_row.datetime)
        self.assertEqual(old_event.text, session_row.description)
        self.assertEqual(old_event.modified_by, None)

    def test_skip_unknown_signature_row(self):
        session_row = SessionRowFactory()
        mock = Mock(get_session_rows=lambda: [session_row])
        self.manager.handle_court(CourtFactory(), mock)
        self.assertEqual(Event.objects.count(), 0)

