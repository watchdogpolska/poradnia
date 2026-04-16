from django.db import migrations

TASK_NAME = "send-event-reminders"
TASK_PATH = "poradnia.events.tasks.send_event_reminders"


def add_periodic_task(apps, schema_editor):
    CrontabSchedule = apps.get_model("django_celery_beat", "CrontabSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="12",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
        timezone="Europe/Warsaw",
    )

    PeriodicTask.objects.update_or_create(
        name=TASK_NAME,
        defaults={
            "task": TASK_PATH,
            "crontab": schedule,
            "interval": None,
            "solar": None,
            "clocked": None,
            "args": "[]",
            "kwargs": "{}",
            "enabled": True,
            "one_off": False,
            "description": "Daily event reminders at 12:00",
        },
    )


def remove_periodic_task(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(name=TASK_NAME, task=TASK_PATH).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0015_event_public"),
        ("django_celery_beat", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_periodic_task, remove_periodic_task),
    ]
