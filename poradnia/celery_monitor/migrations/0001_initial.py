import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SystemHealthCheck",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "singleton_key",
                    models.CharField(default="default", max_length=50, unique=True),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ok", "OK"),
                            ("warn", "Warning"),
                            ("fail", "Failure"),
                        ],
                        default="ok",
                        max_length=10,
                    ),
                ),
                ("db_ok", models.BooleanField(default=False)),
                ("db_latency_ms", models.FloatField(blank=True, null=True)),
                ("db_error", models.TextField(blank=True, default="")),
                ("broker_ok", models.BooleanField(default=False)),
                ("broker_latency_ms", models.FloatField(blank=True, null=True)),
                ("broker_error", models.TextField(blank=True, default="")),
                ("checked_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("task_id", models.CharField(blank=True, default="", max_length=255)),
                (
                    "worker_hostname",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                ("details_json", models.JSONField(blank=True, default=dict)),
            ],
        ),
        migrations.CreateModel(
            name="QueueSnapshot",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("vhost", models.CharField(default="/", max_length=255)),
                ("queue_name", models.CharField(max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ok", "OK"),
                            ("warn", "Warning"),
                            ("crit", "Critical"),
                        ],
                        default="ok",
                        max_length=10,
                    ),
                ),
                ("messages", models.IntegerField(default=0)),
                ("messages_ready", models.IntegerField(default=0)),
                ("messages_unacknowledged", models.IntegerField(default=0)),
                ("consumers", models.IntegerField(default=0)),
                ("checked_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("task_id", models.CharField(blank=True, default="", max_length=255)),
                (
                    "worker_hostname",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                ("details_json", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "ordering": ["queue_name"],
                "unique_together": {("vhost", "queue_name")},
            },
        ),
        migrations.CreateModel(
            name="WorkerHeartbeat",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("worker_name", models.CharField(max_length=255, unique=True)),
                ("hostname", models.CharField(blank=True, default="", max_length=255)),
                ("pid", models.IntegerField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ok", "OK"),
                            ("stale", "Stale"),
                            ("missing", "Missing"),
                        ],
                        default="ok",
                        max_length=10,
                    ),
                ),
                (
                    "last_seen_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "last_task_id",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                ("ping_ok", models.BooleanField(default=False)),
                ("ping_details_json", models.JSONField(blank=True, default=dict)),
            ],
        ),
        migrations.CreateModel(
            name="MonitoringAlert",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source", models.CharField(max_length=100)),
                ("dedupe_key", models.CharField(max_length=255, unique=True)),
                (
                    "severity",
                    models.CharField(
                        choices=[("warn", "Warning"), ("crit", "Critical")],
                        max_length=10,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("message", models.TextField()),
                ("is_resolved", models.BooleanField(default=False)),
                (
                    "first_seen_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "last_seen_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("payload_json", models.JSONField(blank=True, default=dict)),
                ("email_last_sent_at", models.DateTimeField(blank=True, null=True)),
                ("email_send_count", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ["is_resolved", "-last_seen_at"]},
        ),
    ]
