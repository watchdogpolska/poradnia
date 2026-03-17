from django.db import migrations


def seed_periodic_tasks(apps, schema_editor):
    try:
        IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
        PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    except LookupError:
        return

    interval_60, _ = IntervalSchedule.objects.get_or_create(
        every=60,
        period="seconds",
    )
    interval_120, _ = IntervalSchedule.objects.get_or_create(
        every=120,
        period="seconds",
    )

    tasks = [
        {
            "name": "Celery Monitor - healthcheck_task",
            "task": "poradnia.celery_monitor.tasks.healthcheck_task",
            "interval": interval_120,
            "description": "Checks DB and broker connectivity",
        },
        {
            "name": "Celery Monitor - queue_depth_check",
            "task": "poradnia.celery_monitor.tasks.queue_depth_check",
            "interval": interval_60,
            "description": "Checks RabbitMQ queue depth and consumers",
        },
        {
            "name": "Celery Monitor - worker_heartbeat",
            "task": "poradnia.celery_monitor.tasks.worker_heartbeat",
            "interval": interval_60,
            "description": "Records worker liveness and ping data",
        },
        {
            "name": "Celery Monitor - monitor_stale_workers",
            "task": "poradnia.celery_monitor.tasks.monitor_stale_workers",
            "interval": interval_60,
            "description": "Marks stale workers and raises critical alerts",
        },
    ]

    for item in tasks:
        PeriodicTask.objects.get_or_create(
            name=item["name"],
            defaults={
                "task": item["task"],
                "interval": item["interval"],
                "enabled": True,
                "description": item["description"],
            },
        )


def unseed_periodic_tasks(apps, schema_editor):
    try:
        PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    except LookupError:
        return

    PeriodicTask.objects.filter(
        name__in=[
            "Celery Monitor - healthcheck_task",
            "Celery Monitor - queue_depth_check",
            "Celery Monitor - worker_heartbeat",
            "Celery Monitor - monitor_stale_workers",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("celery_monitor", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_periodic_tasks, unseed_periodic_tasks),
    ]
