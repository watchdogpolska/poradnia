from unittest.mock import MagicMock, patch

from django.db import connection as db_connection
from django.test import TestCase, override_settings

from .models import MonitoringAlert, SystemHealthCheck
from .tasks import healthcheck_task


def _make_pool_mock():
    """Pool mock whose acquire context manager yields a healthy producer."""
    producer = MagicMock()
    producer.connection.default_channel = MagicMock()
    pool = MagicMock()
    pool.acquire.return_value.__enter__ = lambda s, *a, **kw: producer
    pool.acquire.return_value.__exit__ = MagicMock(return_value=False)
    return pool


def _make_pool_error(exc):
    """Pool mock whose acquire context manager raises exc."""
    pool = MagicMock()
    pool.acquire.return_value.__enter__ = MagicMock(side_effect=exc)
    pool.acquire.return_value.__exit__ = MagicMock(return_value=False)
    return pool


def _db_fail_once(message="db gone"):
    """
    Returns a side_effect callable for patching connection.cursor.
    The first call (the SELECT 1 probe) raises; all subsequent calls
    (ORM savepoints, update_or_create, etc.) pass through to the real cursor.
    """
    real_cursor = db_connection.cursor
    calls = []

    def side_effect(*args, **kwargs):
        if not calls:
            calls.append(True)
            raise Exception(message)
        return real_cursor(*args, **kwargs)

    return side_effect


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    ADMINS=[],  # suppress email sending
)
class HealthcheckTaskTest(TestCase):
    def _run(self, pool_mock):
        with patch.object(healthcheck_task, "app", MagicMock(pool=pool_mock)):
            healthcheck_task.apply().get()

    def _run_db_fail(self, pool_mock, message="db gone"):
        with patch.object(db_connection, "cursor", side_effect=_db_fail_once(message)):
            self._run(pool_mock)

    # --- happy path ---

    def test_both_ok_creates_ok_record(self):
        self._run(_make_pool_mock())

        hc = SystemHealthCheck.objects.get(singleton_key="default")
        self.assertEqual(hc.status, SystemHealthCheck.STATUS_OK)
        self.assertTrue(hc.db_ok)
        self.assertTrue(hc.broker_ok)
        self.assertEqual(hc.db_error, "")
        self.assertEqual(hc.broker_error, "")
        self.assertIsNotNone(hc.db_latency_ms)
        self.assertIsNotNone(hc.broker_latency_ms)

    def test_second_run_updates_record_not_duplicates(self):
        self._run(_make_pool_mock())
        self._run(_make_pool_mock())

        self.assertEqual(SystemHealthCheck.objects.count(), 1)

    def test_both_ok_resolves_existing_alert(self):
        MonitoringAlert.objects.create(
            source="healthcheck_task",
            dedupe_key="healthcheck:default",
            severity=MonitoringAlert.SEVERITY_CRIT,
            title="old",
            message="old",
            is_resolved=False,
        )

        self._run(_make_pool_mock())

        alert = MonitoringAlert.objects.get(dedupe_key="healthcheck:default")
        self.assertTrue(alert.is_resolved)

    # --- broker failure ---

    def test_broker_fail_creates_fail_record_and_alert(self):
        self._run(_make_pool_error(Exception("timed out")))

        hc = SystemHealthCheck.objects.get(singleton_key="default")
        self.assertEqual(hc.status, SystemHealthCheck.STATUS_FAIL)
        self.assertTrue(hc.db_ok)
        self.assertFalse(hc.broker_ok)
        self.assertIn("timed out", hc.broker_error)
        self.assertIsNotNone(hc.broker_latency_ms)

        alert = MonitoringAlert.objects.get(dedupe_key="healthcheck:default")
        self.assertFalse(alert.is_resolved)
        self.assertEqual(alert.severity, MonitoringAlert.SEVERITY_CRIT)

    # --- db failure ---

    def test_db_fail_creates_fail_record_and_alert(self):
        self._run_db_fail(_make_pool_mock())

        hc = SystemHealthCheck.objects.get(singleton_key="default")
        self.assertEqual(hc.status, SystemHealthCheck.STATUS_FAIL)
        self.assertFalse(hc.db_ok)
        self.assertTrue(hc.broker_ok)
        self.assertIn("db gone", hc.db_error)

        alert = MonitoringAlert.objects.get(dedupe_key="healthcheck:default")
        self.assertFalse(alert.is_resolved)
        self.assertEqual(alert.severity, MonitoringAlert.SEVERITY_CRIT)

    # --- both fail ---

    def test_both_fail_creates_single_alert(self):
        self._run_db_fail(_make_pool_error(Exception("broker gone")))

        hc = SystemHealthCheck.objects.get(singleton_key="default")
        self.assertEqual(hc.status, SystemHealthCheck.STATUS_FAIL)
        self.assertFalse(hc.db_ok)
        self.assertFalse(hc.broker_ok)

        self.assertEqual(MonitoringAlert.objects.filter(is_resolved=False).count(), 1)

    # --- recovery ---

    def test_recovery_resolves_alert(self):
        self._run(_make_pool_error(Exception("down")))
        alert = MonitoringAlert.objects.get(dedupe_key="healthcheck:default")
        self.assertFalse(alert.is_resolved)

        self._run(_make_pool_mock())
        alert.refresh_from_db()
        self.assertTrue(alert.is_resolved)
