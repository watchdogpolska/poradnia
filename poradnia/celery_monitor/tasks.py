import json
import logging
import os
import socket
import time
import urllib.request
from urllib.parse import quote

from celery import shared_task
from django.conf import settings
from django.core.mail import mail_admins
from django.db import connection
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from kombu import Connection

from .models import (
    MonitoringAlert,
    QueueSnapshot,
    SystemHealthCheck,
    TaskSlaSnapshot,
    WorkerHeartbeat,
)

logger = logging.getLogger(__name__)


def rabbit_api(path):
    url = settings.RABBITMQ_API_URL.rstrip("/") + "/" + path.lstrip("/")
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(
        None,
        url,
        settings.RABBITMQ_API_USER,
        settings.RABBITMQ_API_PASSWORD,
    )
    auth = urllib.request.HTTPBasicAuthHandler(password_mgr)
    opener = urllib.request.build_opener(auth)
    with opener.open(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_setting(name, default):
    return getattr(settings, name, default)


def _should_send_alert_email(alert):
    cooldown_seconds = int(
        _get_setting("CELERY_MONITOR_ALERT_EMAIL_COOLDOWN_SECONDS", 3600)
    )
    if not alert.email_last_sent_at:
        return True
    cutoff = timezone.now() - timezone.timedelta(seconds=cooldown_seconds)
    return alert.email_last_sent_at < cutoff


def _send_alert_email(alert):
    recipients_configured = bool(getattr(settings, "ADMINS", None))
    enabled = bool(_get_setting("CELERY_MONITOR_EMAIL_ALERTS_ENABLED", True))
    if not enabled or not recipients_configured:
        return False

    if not _should_send_alert_email(alert):
        return False

    subject_prefix = _get_setting(
        "CELERY_MONITOR_EMAIL_SUBJECT_PREFIX", "[Celery Monitor]"
    )
    subject = f"{subject_prefix} {alert.title}"
    body = (
        f"Severity: {alert.severity}\n"
        f"Source: {alert.source}\n"
        f"Dedupe key: {alert.dedupe_key}\n"
        f"First seen: {alert.first_seen_at.isoformat()}\n"
        f"Last seen: {alert.last_seen_at.isoformat()}\n"
        f"Resolved: {alert.is_resolved}\n\n"
        f"{alert.message}\n\n"
        f"Payload:\n{json.dumps(alert.payload_json, indent=2, sort_keys=True)}"
    )

    mail_admins(subject=subject, message=body, fail_silently=True)
    alert.email_last_sent_at = timezone.now()
    alert.email_send_count += 1
    alert.save(update_fields=["email_last_sent_at", "email_send_count", "updated_at"])
    return True


def _create_or_touch_alert(*, source, dedupe_key, severity, title, message, payload):
    now = timezone.now()
    alert, created = MonitoringAlert.objects.get_or_create(
        dedupe_key=dedupe_key,
        defaults={
            "source": source,
            "severity": severity,
            "title": title,
            "message": message,
            "payload_json": payload,
            "first_seen_at": now,
            "last_seen_at": now,
        },
    )
    if not created:
        alert.source = source
        alert.severity = severity
        alert.title = title
        alert.message = message
        alert.payload_json = payload
        alert.last_seen_at = now
        alert.is_resolved = False
        alert.resolved_at = None
        alert.save(
            update_fields=[
                "source",
                "severity",
                "title",
                "message",
                "payload_json",
                "last_seen_at",
                "is_resolved",
                "resolved_at",
                "updated_at",
            ]
        )
    if alert.severity == MonitoringAlert.SEVERITY_CRIT:
        _send_alert_email(alert)
    return alert


def _resolve_alert(dedupe_key):
    MonitoringAlert.objects.filter(
        dedupe_key=dedupe_key,
        is_resolved=False,
    ).update(
        is_resolved=True,
        resolved_at=timezone.now(),
        last_seen_at=timezone.now(),
    )


# Added in migration 0002_seed_monitor_periodic_tasks.py to celery beat db table
@shared_task(bind=True, ignore_result=True)
def healthcheck_task(self):
    checked_at = timezone.now()

    db_ok = False
    db_latency_ms = None
    db_error = ""

    broker_ok = False
    broker_latency_ms = None
    broker_error = ""

    start = time.monotonic()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
        db_ok = row == (1,)
        db_latency_ms = round((time.monotonic() - start) * 1000, 2)
    except Exception as exc:
        db_error = str(exc)
        logger.exception("Database healthcheck failed")

    start = time.monotonic()
    try:
        with Connection(settings.CELERY_BROKER_URL, connect_timeout=5) as conn:
            conn.connect()
        broker_ok = True
        broker_latency_ms = round((time.monotonic() - start) * 1000, 2)
    except Exception as exc:
        broker_error = str(exc)
        logger.exception("Broker healthcheck failed")

    status = (
        SystemHealthCheck.STATUS_OK
        if (db_ok and broker_ok)
        else SystemHealthCheck.STATUS_FAIL
    )

    obj, _ = SystemHealthCheck.objects.update_or_create(
        singleton_key="default",
        defaults={
            "status": status,
            "db_ok": db_ok,
            "db_latency_ms": db_latency_ms,
            "db_error": db_error,
            "broker_ok": broker_ok,
            "broker_latency_ms": broker_latency_ms,
            "broker_error": broker_error,
            "checked_at": checked_at,
            "task_id": self.request.id or "",
            "worker_hostname": self.request.hostname or "",
            "details_json": {},
        },
    )

    dedupe_key = "healthcheck:default"
    if status == SystemHealthCheck.STATUS_FAIL:
        _create_or_touch_alert(
            source="healthcheck_task",
            dedupe_key=dedupe_key,
            severity=MonitoringAlert.SEVERITY_CRIT,
            title="Celery system healthcheck failed",
            message=f"db_ok={db_ok}, broker_ok={broker_ok}",
            payload={
                "db_error": db_error,
                "broker_error": broker_error,
                "checked_at": checked_at.isoformat(),
            },
        )
    else:
        _resolve_alert(dedupe_key)

    return {
        "status": obj.status,
        "db_ok": obj.db_ok,
        "broker_ok": obj.broker_ok,
        "checked_at": obj.checked_at.isoformat(),
    }


# Added in migration 0002_seed_monitor_periodic_tasks.py to celery beat db table
@shared_task(bind=True, ignore_result=True)
def queue_depth_check(self):
    api_url = settings.RABBITMQ_API_URL.rstrip("/")
    api_user = settings.RABBITMQ_API_USER
    api_password = settings.RABBITMQ_API_PASSWORD

    if not api_url or not api_user or not api_password:
        raise RuntimeError(
            "RabbitMQ management API credentials are not fully configured"
        )

    vhost = _get_setting("CELERY_MONITOR_VHOST", "/")
    queues_to_monitor = _get_setting("CELERY_MONITOR_QUEUES", ["celery"])

    ready_warn = int(_get_setting("CELERY_QUEUE_READY_WARN", 100))
    ready_crit = int(_get_setting("CELERY_QUEUE_READY_CRIT", 1000))
    unack_warn = int(_get_setting("CELERY_QUEUE_UNACK_WARN", 50))
    unack_crit = int(_get_setting("CELERY_QUEUE_UNACK_CRIT", 300))

    queues = rabbit_api(f"api/queues/{quote(vhost, safe='')}")
    queue_map = {q["name"]: q for q in queues}
    results = {}

    for queue_name in queues_to_monitor:
        q = queue_map.get(queue_name)
        if not q:
            QueueSnapshot.objects.update_or_create(
                vhost=vhost,
                queue_name=queue_name,
                defaults={
                    "status": QueueSnapshot.STATUS_CRIT,
                    "messages": 0,
                    "messages_ready": 0,
                    "messages_unacknowledged": 0,
                    "consumers": 0,
                    "checked_at": timezone.now(),
                    "task_id": self.request.id or "",
                    "worker_hostname": self.request.hostname or "",
                    "details_json": {"error": "queue_not_found"},
                },
            )
            _create_or_touch_alert(
                source="queue_depth_check",
                dedupe_key=f"queue:{vhost}:{queue_name}:missing",
                severity=MonitoringAlert.SEVERITY_CRIT,
                title=f"Queue missing: {queue_name}",
                message=f"Queue {queue_name!r} not found in vhost {vhost!r}",
                payload={"vhost": vhost, "queue_name": queue_name},
            )
            results[queue_name] = {"status": "crit", "error": "queue_not_found"}
            continue

        ready = int(q.get("messages_ready", 0))
        unack = int(q.get("messages_unacknowledged", 0))
        messages = int(q.get("messages", 0))
        consumers = int(q.get("consumers", 0))

        if ready >= ready_crit or unack >= unack_crit or consumers == 0:
            status = QueueSnapshot.STATUS_CRIT
        elif ready >= ready_warn or unack >= unack_warn:
            status = QueueSnapshot.STATUS_WARN
        else:
            status = QueueSnapshot.STATUS_OK

        QueueSnapshot.objects.update_or_create(
            vhost=vhost,
            queue_name=queue_name,
            defaults={
                "status": status,
                "messages": messages,
                "messages_ready": ready,
                "messages_unacknowledged": unack,
                "consumers": consumers,
                "checked_at": timezone.now(),
                "task_id": self.request.id or "",
                "worker_hostname": self.request.hostname or "",
                "details_json": {},
            },
        )

        backlog_alert_key = f"queue:{vhost}:{queue_name}:depth"
        if status == QueueSnapshot.STATUS_CRIT:
            _create_or_touch_alert(
                source="queue_depth_check",
                dedupe_key=backlog_alert_key,
                severity=MonitoringAlert.SEVERITY_CRIT,
                title=f"Queue backlog critical: {queue_name}",
                message=f"ready={ready}, unack={unack}, consumers={consumers}",
                payload={
                    "vhost": vhost,
                    "queue_name": queue_name,
                    "messages": messages,
                    "messages_ready": ready,
                    "messages_unacknowledged": unack,
                    "consumers": consumers,
                },
            )
        elif status == QueueSnapshot.STATUS_WARN:
            _create_or_touch_alert(
                source="queue_depth_check",
                dedupe_key=backlog_alert_key,
                severity=MonitoringAlert.SEVERITY_WARN,
                title=f"Queue backlog warning: {queue_name}",
                message=f"ready={ready}, unack={unack}, consumers={consumers}",
                payload={
                    "vhost": vhost,
                    "queue_name": queue_name,
                    "messages": messages,
                    "messages_ready": ready,
                    "messages_unacknowledged": unack,
                    "consumers": consumers,
                },
            )
        else:
            _resolve_alert(backlog_alert_key)
            _resolve_alert(f"queue:{vhost}:{queue_name}:missing")

        results[queue_name] = {
            "status": status,
            "messages": messages,
            "messages_ready": ready,
            "messages_unacknowledged": unack,
            "consumers": consumers,
        }

    return results


# Added in migration 0002_seed_monitor_periodic_tasks.py to celery beat db table
@shared_task(bind=True, ignore_result=True)
def worker_heartbeat(self):
    """
    Record that a worker actually consumed and executed this task.

    For this monitor, successful task execution is the primary worker-liveness
    signal. We intentionally do not use Celery remote-control ping here,
    because self-ping from inside a running worker task is noisy and can
    produce false negatives in containerized deployments.
    """
    worker_name = self.request.hostname or f"unknown@{socket.gethostname()}"
    now = timezone.now()

    obj, _ = WorkerHeartbeat.objects.update_or_create(
        worker_name=worker_name,
        defaults={
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
            "status": WorkerHeartbeat.STATUS_OK,
            "last_seen_at": now,
            "last_task_id": self.request.id or "",
            "ping_ok": True,
            "ping_details_json": {
                "mode": "task_execution_heartbeat",
                "note": (
                    "Worker heartbeat confirmed by successful execution of "
                    "worker_heartbeat task; remote-control ping intentionally skipped."
                ),
            },
        },
    )

    _resolve_alert(f"worker:{worker_name}:stale")

    return {
        "worker_name": obj.worker_name,
        "status": obj.status,
        "last_seen_at": obj.last_seen_at.isoformat(),
        "ping_ok": obj.ping_ok,
    }


# Added in migration 0002_seed_monitor_periodic_tasks.py to celery beat db table
@shared_task(bind=True, ignore_result=True)
def monitor_stale_workers(self):
    """
    Marks workers stale if heartbeat is too old.

    Containerized deployments often produce old worker rows after container
    recreation because the Celery worker hostname changes. To avoid permanent
    noise, very old worker rows are deleted automatically.
    """
    now = timezone.now()

    stale_after_seconds = int(_get_setting("CELERY_WORKER_STALE_AFTER_SECONDS", 180))
    cleanup_after_seconds = int(
        _get_setting("CELERY_MONITOR_WORKER_CLEANUP_AFTER_SECONDS", 86400)
    )

    stale_cutoff = now - timezone.timedelta(seconds=stale_after_seconds)
    cleanup_cutoff = now - timezone.timedelta(seconds=cleanup_after_seconds)

    # 1. Hard-delete ancient worker rows from long-gone containers
    deleted_count, _ = WorkerHeartbeat.objects.filter(
        last_seen_at__lt=cleanup_cutoff
    ).delete()

    # 2. Fresh workers remain OK
    WorkerHeartbeat.objects.filter(last_seen_at__gte=stale_cutoff).exclude(
        status=WorkerHeartbeat.STATUS_OK
    ).update(status=WorkerHeartbeat.STATUS_OK)

    # 3. Recent-but-missed workers become stale
    stale_workers = WorkerHeartbeat.objects.filter(
        last_seen_at__lt=stale_cutoff,
        last_seen_at__gte=cleanup_cutoff,
    )

    stale_count = 0

    for worker in stale_workers:
        if worker.status != WorkerHeartbeat.STATUS_STALE:
            worker.status = WorkerHeartbeat.STATUS_STALE
            worker.save(update_fields=["status", "updated_at"])

        _create_or_touch_alert(
            source="monitor_stale_workers",
            dedupe_key=f"worker:{worker.worker_name}:stale",
            severity=MonitoringAlert.SEVERITY_CRIT,
            title=f"Celery worker stale: {worker.worker_name}",
            message=f"Last seen at {worker.last_seen_at.isoformat()}",
            payload={
                "worker_name": worker.worker_name,
                "hostname": worker.hostname,
                "pid": worker.pid,
                "last_seen_at": worker.last_seen_at.isoformat(),
                "stale_after_seconds": stale_after_seconds,
            },
        )
        stale_count += 1

    return {
        "stale_workers": stale_count,
        "deleted_old_workers": deleted_count,
    }


@shared_task(bind=True, ignore_result=True)
def enqueue_sla_probe(self):
    """
    Beat calls this task. It immediately enqueues the actual worker-side probe
    carrying the enqueue timestamp.
    """
    now = timezone.now()
    queue_names = _get_setting(
        "CELERY_MONITOR_QUEUES",
        [
            "poradnia",
        ],
    )
    for queue_name in queue_names:
        sla_probe_worker.apply_async(
            kwargs={
                "enqueued_at_iso": now.isoformat(),
                "queue_name": queue_name,
            },
            queue=queue_name,
        )

    return {
        "status": "enqueued",
        "queue_names": queue_names,
        "enqueued_at": now.isoformat(),
    }


@shared_task(bind=True, ignore_result=True)
def sla_probe_worker(self, enqueued_at_iso, queue_name=""):
    """
    Measures queue-to-worker lag:
    how long it took from enqueue until actual execution start.
    """
    started_at = timezone.now()
    enqueued_at = parse_datetime(enqueued_at_iso)

    if enqueued_at is None:
        raise ValueError(f"Invalid enqueued_at_iso: {enqueued_at_iso!r}")

    lag_ms = int((started_at - enqueued_at).total_seconds() * 1000)

    warn_ms = int(_get_setting("CELERY_MONITOR_SLA_WARN_MS", 15000))
    crit_ms = int(_get_setting("CELERY_MONITOR_SLA_CRIT_MS", 60000))

    if lag_ms >= crit_ms:
        status = TaskSlaSnapshot.STATUS_CRIT
    elif lag_ms >= warn_ms:
        status = TaskSlaSnapshot.STATUS_WARN
    else:
        status = TaskSlaSnapshot.STATUS_OK

    obj, _ = TaskSlaSnapshot.objects.update_or_create(
        probe_name="default",
        defaults={
            "queue_name": queue_name,
            "status": status,
            "enqueued_at": enqueued_at,
            "started_at": started_at,
            "lag_ms": lag_ms,
            "task_id": self.request.id or "",
            "worker_hostname": self.request.hostname or "",
            "details_json": {},
        },
    )

    dedupe_key = "sla_probe:default"
    if status == TaskSlaSnapshot.STATUS_CRIT:
        _create_or_touch_alert(
            source="sla_probe_worker",
            dedupe_key=dedupe_key,
            severity=MonitoringAlert.SEVERITY_CRIT,
            title="Celery task consumption lag critical",
            message=f"lag_ms={lag_ms}, queue={queue_name}",
            payload={
                "lag_ms": lag_ms,
                "warn_ms": warn_ms,
                "crit_ms": crit_ms,
                "queue_name": queue_name,
                "worker_hostname": obj.worker_hostname,
                "enqueued_at": enqueued_at.isoformat(),
                "started_at": started_at.isoformat(),
            },
        )
    elif status == TaskSlaSnapshot.STATUS_WARN:
        _create_or_touch_alert(
            source="sla_probe_worker",
            dedupe_key=dedupe_key,
            severity=MonitoringAlert.SEVERITY_WARN,
            title="Celery task consumption lag warning",
            message=f"lag_ms={lag_ms}, queue={queue_name}",
            payload={
                "lag_ms": lag_ms,
                "warn_ms": warn_ms,
                "crit_ms": crit_ms,
                "queue_name": queue_name,
                "worker_hostname": obj.worker_hostname,
                "enqueued_at": enqueued_at.isoformat(),
                "started_at": started_at.isoformat(),
            },
        )
    else:
        _resolve_alert(dedupe_key)

    return {
        "status": status,
        "lag_ms": lag_ms,
        "queue_name": queue_name,
        "worker_hostname": obj.worker_hostname,
    }
