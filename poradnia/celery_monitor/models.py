from django.db import models
from django.utils import timezone


class MonitorBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SystemHealthCheck(MonitorBaseModel):
    STATUS_OK = "ok"
    STATUS_WARN = "warn"
    STATUS_FAIL = "fail"
    STATUS_CHOICES = [
        (STATUS_OK, "OK"),
        (STATUS_WARN, "Warning"),
        (STATUS_FAIL, "Failure"),
    ]

    singleton_key = models.CharField(max_length=50, unique=True, default="default")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OK)

    db_ok = models.BooleanField(default=False)
    db_latency_ms = models.FloatField(null=True, blank=True)
    db_error = models.TextField(blank=True, default="")

    broker_ok = models.BooleanField(default=False)
    broker_latency_ms = models.FloatField(null=True, blank=True)
    broker_error = models.TextField(blank=True, default="")

    checked_at = models.DateTimeField(default=timezone.now)
    task_id = models.CharField(max_length=255, blank=True, default="")
    worker_hostname = models.CharField(max_length=255, blank=True, default="")
    details_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"SystemHealthCheck({self.status})"


class QueueSnapshot(MonitorBaseModel):
    STATUS_OK = "ok"
    STATUS_WARN = "warn"
    STATUS_CRIT = "crit"
    STATUS_CHOICES = [
        (STATUS_OK, "OK"),
        (STATUS_WARN, "Warning"),
        (STATUS_CRIT, "Critical"),
    ]

    vhost = models.CharField(max_length=255, default="/")
    queue_name = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OK)

    messages = models.IntegerField(default=0)
    messages_ready = models.IntegerField(default=0)
    messages_unacknowledged = models.IntegerField(default=0)
    consumers = models.IntegerField(default=0)

    checked_at = models.DateTimeField(default=timezone.now)
    task_id = models.CharField(max_length=255, blank=True, default="")
    worker_hostname = models.CharField(max_length=255, blank=True, default="")
    details_json = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [("vhost", "queue_name")]
        ordering = ["queue_name"]

    def __str__(self):
        return f"{self.vhost}:{self.queue_name}"


class WorkerHeartbeat(MonitorBaseModel):
    STATUS_OK = "ok"
    STATUS_STALE = "stale"
    STATUS_MISSING = "missing"
    STATUS_CHOICES = [
        (STATUS_OK, "OK"),
        (STATUS_STALE, "Stale"),
        (STATUS_MISSING, "Missing"),
    ]

    worker_name = models.CharField(max_length=255, unique=True)
    hostname = models.CharField(max_length=255, blank=True, default="")
    pid = models.IntegerField(null=True, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OK)
    last_seen_at = models.DateTimeField(default=timezone.now)

    last_task_id = models.CharField(max_length=255, blank=True, default="")
    ping_ok = models.BooleanField(default=False)
    ping_details_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.worker_name


class MonitoringAlert(MonitorBaseModel):
    SEVERITY_WARN = "warn"
    SEVERITY_CRIT = "crit"
    SEVERITY_CHOICES = [
        (SEVERITY_WARN, "Warning"),
        (SEVERITY_CRIT, "Critical"),
    ]

    source = models.CharField(max_length=100)
    dedupe_key = models.CharField(max_length=255, unique=True)

    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()

    is_resolved = models.BooleanField(default=False)
    first_seen_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)

    payload_json = models.JSONField(default=dict, blank=True)

    email_last_sent_at = models.DateTimeField(null=True, blank=True)
    email_send_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["is_resolved", "-last_seen_at"]

    def __str__(self):
        return f"[{self.severity}] {self.title}"


class TaskSlaSnapshot(MonitorBaseModel):
    STATUS_OK = "ok"
    STATUS_WARN = "warn"
    STATUS_CRIT = "crit"
    STATUS_CHOICES = [
        (STATUS_OK, "OK"),
        (STATUS_WARN, "Warning"),
        (STATUS_CRIT, "Critical"),
    ]

    probe_name = models.CharField(max_length=100, unique=True, default="default")
    queue_name = models.CharField(max_length=255, blank=True, default="")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OK)

    enqueued_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    lag_ms = models.IntegerField(default=0)

    task_id = models.CharField(max_length=255, blank=True, default="")
    worker_hostname = models.CharField(max_length=255, blank=True, default="")

    details_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.probe_name} ({self.status})"
