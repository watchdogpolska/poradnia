from django.db import migrations


def add_sla_probe_task(apps, schema_editor):
    IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    interval, _ = IntervalSchedule.objects.get_or_create(
        every=60,
        period="seconds",
    )

    PeriodicTask.objects.get_or_create(
        name="Celery Monitor - enqueue_sla_probe",
        defaults={
            "task": "poradnia.celery_monitor.tasks.enqueue_sla_probe",
            "interval": interval,
            "enabled": True,
            "description": "Celery monitoring SLA probe (task consumption latency)",
        },
    )


def remove_sla_probe_task(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    PeriodicTask.objects.filter(name="Celery Monitor - enqueue_sla_probe").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("django_celery_beat", "0001_initial"),
        ("celery_monitor", "0003_taskslasnapshot"),
    ]

    operations = [
        migrations.RunPython(add_sla_probe_task, remove_sla_probe_task),
    ]
