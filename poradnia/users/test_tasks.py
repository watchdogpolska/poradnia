from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase
from django.utils import timezone

from poradnia.users.tasks import clear_expired_sessions


def _create_session(expire_offset_seconds):
    store = SessionStore()
    store.create()
    store.set_expiry(expire_offset_seconds)
    store.save()
    from django.contrib.sessions.models import Session

    session = Session.objects.get(session_key=store.session_key)
    if expire_offset_seconds < 0:
        session.expire_date = timezone.now() + timezone.timedelta(
            seconds=expire_offset_seconds
        )
        session.save(update_fields=["expire_date"])
    return store.session_key


class ClearExpiredSessionsTaskTestCase(TestCase):
    def _run(self):
        return clear_expired_sessions.apply().result

    def test_returns_deleted_count_zero_when_no_sessions(self):
        result = self._run()
        self.assertEqual(result["deleted"], 0)

    def test_deletes_expired_session(self):
        _create_session(expire_offset_seconds=-1)
        result = self._run()
        self.assertEqual(result["deleted"], 1)

    def test_does_not_delete_valid_session(self):
        _create_session(expire_offset_seconds=3600)
        result = self._run()
        self.assertEqual(result["deleted"], 0)

    def test_deletes_only_expired_sessions(self):
        _create_session(expire_offset_seconds=-1)
        _create_session(expire_offset_seconds=-1)
        _create_session(expire_offset_seconds=3600)
        result = self._run()
        self.assertEqual(result["deleted"], 2)


class ClearExpiredSessionsCommandTestCase(TestCase):
    def test_command_output(self):
        from io import StringIO

        from django.core.management import call_command

        _create_session(expire_offset_seconds=-1)
        out = StringIO()
        call_command("clear_expired_sessions", stdout=out)
        self.assertIn("deleted=1", out.getvalue())
