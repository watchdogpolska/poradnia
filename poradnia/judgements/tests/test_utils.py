import datetime

from poradnia.judgements.tests.test_parsers import my_vcr

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from unittest import mock

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from poradnia.cases.factories import CaseUserObjectPermissionFactory
from poradnia.events.models import Event
from poradnia.judgements import settings
from poradnia.judgements.factories import (
    CourtCaseFactory,
    CourtFactory,
    CourtSessionFactory,
    SessionRowFactory,
)
from poradnia.judgements.utils import Manager
from poradnia.users.factories import UserFactory


class ManagerTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory(username=settings.JUDGEMENT_BOT_USERNAME)
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.manager = Manager(bot=self.user, stdout=self.stdout, stderr=self.stderr)

    def test_create_new_event(self):
        courtcase = CourtCaseFactory()
        session_row = SessionRowFactory(signature=courtcase.signature)
        my_mock = mock.Mock(get_session_rows=lambda: [session_row])
        self.manager.handle_court(courtcase.court, my_mock)
        event = Event.objects.get()
        self.assertEqual(event.time, session_row.datetime)
        self.assertEqual(event.text, session_row.description)

    def test_notify_about_create_new_event(self):
        cuop = CaseUserObjectPermissionFactory(
            user__is_staff=True, permission_name="can_send_to_client"
        )

        courtcase = CourtCaseFactory(case=cuop.content_object)
        session_row = SessionRowFactory(signature=courtcase.signature)
        my_mock = mock.Mock(get_session_rows=lambda: [session_row])
        self.manager.handle_court(courtcase.court, my_mock)

        self.assertEqual(len(mail.outbox), 1)
        new_mail = mail.outbox.pop()

        self.assertIn(courtcase.signature, new_mail.body)

    def test_update_event_text_on_new_session_row_text(self):
        courtsession = CourtSessionFactory()
        courtcase = courtsession.courtcase
        old_event = courtsession.event
        session_row = SessionRowFactory(
            signature=courtcase.signature, datetime=old_event.time
        )
        my_mock = mock.Mock(get_session_rows=lambda: [session_row])
        self.manager.handle_court(courtsession.courtcase.court, my_mock)
        self.assertEqual(Event.objects.count(), 1)
        old_event.refresh_from_db()
        self.assertEqual(old_event.time, session_row.datetime)
        self.assertEqual(old_event.text, session_row.description)
        self.assertEqual(old_event.modified_by, self.user)

    def test_notify_about_update_event(self):
        cuop = CaseUserObjectPermissionFactory(
            user__is_staff=True, permission_name="can_send_to_client"
        )

        courtcase = CourtCaseFactory(case=cuop.content_object)
        session_row = SessionRowFactory(signature=courtcase.signature)
        my_mock = mock.Mock(get_session_rows=lambda: [session_row])
        self.manager.handle_court(courtcase.court, my_mock)

        self.assertEqual(len(mail.outbox), 1)
        new_mail = mail.outbox.pop()

        self.assertIn(courtcase.signature, new_mail.body)

    def test_skip_update_and_notification_if_event_completed(self):
        # regression: a court session's time/description getting corrected
        # upstream after a human already marked the local event completed
        # used to silently reopen it and re-notify staff.
        old_time = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        courtsession = CourtSessionFactory(event__time=old_time)
        courtcase = courtsession.courtcase
        old_event = courtsession.event
        old_text = old_event.text
        old_event.completed = True
        old_event.save()
        session_row = SessionRowFactory(
            signature=courtcase.signature,
            datetime=old_time + datetime.timedelta(hours=1),
        )
        my_mock = mock.Mock(get_session_rows=lambda: [session_row])
        self.manager.handle_court(courtsession.courtcase.court, my_mock)
        old_event.refresh_from_db()
        self.assertEqual(old_event.text, old_text)
        self.assertEqual(old_event.time, old_time)
        self.assertIsNone(old_event.modified_by)
        self.assertEqual(len(mail.outbox), 0)

    def test_skip_update_event_if_session_row_match(self):
        courtsession = CourtSessionFactory()
        courtcase = courtsession.courtcase
        old_event = courtsession.event
        session_row = SessionRowFactory(
            signature=courtcase.signature,
            datetime=old_event.time,
            description=old_event.text,
        )
        my_mock = mock.Mock(get_session_rows=lambda: [session_row])
        self.manager.handle_court(courtsession.courtcase.court, my_mock)
        self.assertEqual(Event.objects.count(), 1)
        old_event.refresh_from_db()
        self.assertEqual(old_event.time, session_row.datetime)
        self.assertEqual(old_event.text, session_row.description)
        self.assertEqual(old_event.modified_by, None)

    def test_skip_unknown_signature_row(self):
        session_row = SessionRowFactory()
        my_mock = mock.Mock(get_session_rows=lambda: [session_row])
        self.manager.handle_court(CourtFactory(), my_mock)
        self.assertEqual(Event.objects.count(), 0)

    @my_vcr.use_cassette()
    def test_against_unnecessary_changes(self):
        courtcase = CourtCaseFactory(
            court__parser_key="WSA_Gdansk", signature="II SA/Gd 486/21"
        )
        CaseUserObjectPermissionFactory(
            content_object=courtcase.case,
            permission_name="can_send_to_client",
            user__is_staff=True,
        )
        self.manager.handle_court(courtcase.court)
        self.assertTrue(len(mail.outbox) == 1, "Missing creation notification send")
        self.manager.handle_court(courtcase.court)
        self.assertTrue(len(mail.outbox) == 1, "Abused update notification send")
