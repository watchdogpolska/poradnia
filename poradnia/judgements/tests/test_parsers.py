# -*- coding: utf-8 -*-
# import inspect
import datetime
import inspect
import os

from django.test import TestCase
from django.utils import six
from pytz import timezone
from vcr import VCR

from poradnia.judgements.factories import CourtFactory
from poradnia.judgements.parsers.gliwice import GliwiceETRParser
from poradnia.judgements.registry import get_parser_keys

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
                    msg = "Failed for {} in {}.".format(i, parser_key)
                    self.assertTrue(session_row.signature, msg=msg + "Missing signature")
                    self.assertTrue(session_row.datetime, msg=msg + "Missing datetime")
                    self.assertTrue(session_row.description, msg=msg + "Missing description")
                    self.assertIn(member=session_row.signature,
                                  container=session_row.description,
                                  msg=msg + "Missing signature in description")

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

    @my_vcr.use_cassette()
    def test_parse_date_and_hours(self):
        expected_time = datetime.datetime(2018, 4, 24, 9, 0, tzinfo=timezone('Europe/Warsaw'))
        session_row = next(CourtFactory().get_parser().get_session_rows())
        self.assertAlmostEqual(expected_time, session_row.datetime, delta=datetime.timedelta(seconds=1))
