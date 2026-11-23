from django.conf import settings
from django.db import migrations

TASK_PATH = "poradnia.ai_assistant.tasks.sync_similar_cases_index_task"

# Created disabled: enable them in the admin after the initial index load.
PERIODIC_TASKS = (
    {
        "name": "sync-similar-cases-index-incremental",
        "crontab": {"minute": "17", "hour": "2", "day_of_week": "*"},
        "kwargs": '{"mode": "incremental"}',
        "description": "Nightly incremental sync of the similar cases index at 02:17",
    },
    {
        "name": "sync-similar-cases-index-reconcile",
        "crontab": {"minute": "23", "hour": "3", "day_of_week": "0"},
        "kwargs": '{"mode": "reconcile"}',
        "description": "Weekly reconcile of the similar cases index, Sunday 03:23",
    },
)


def add_periodic_tasks(apps, schema_editor):
    CrontabSchedule = apps.get_model("django_celery_beat", "CrontabSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    for task in PERIODIC_TASKS:
        schedule, _ = CrontabSchedule.objects.get_or_create(
            day_of_month="*",
            month_of_year="*",
            timezone=settings.TIME_ZONE,
            **task["crontab"],
        )
        PeriodicTask.objects.update_or_create(
            name=task["name"],
            defaults={
                "task": TASK_PATH,
                "crontab": schedule,
                "interval": None,
                "args": "[]",
                "kwargs": task["kwargs"],
                "enabled": False,
                "description": task["description"],
            },
        )


def remove_periodic_tasks(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(
        name__in=[task["name"] for task in PERIODIC_TASKS], task=TASK_PATH
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0007_similar_cases"),
        ("django_celery_beat", "0019_alter_periodictasks_options"),
    ]

    operations = [
        migrations.RunPython(add_periodic_tasks, remove_periodic_tasks),
    ]
