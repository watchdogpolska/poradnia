from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("events", "0004_auto_20150322_0543")]

    operations = [
        migrations.AlterModelOptions(
            name="alarm",
            options={"verbose_name": "Alarm", "verbose_name_plural": "Alarms"},
        ),
        migrations.AlterModelOptions(
            name="event",
            options={"verbose_name": "Event", "verbose_name_plural": "Events"},
        ),
        migrations.AlterField(
            model_name="event",
            name="created_by",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="event_created_by",
                verbose_name="Created by",
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="event",
            name="created_on",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created on"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="event",
            name="deadline",
            field=models.BooleanField(default=False, verbose_name="Dead-line"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="event",
            name="for_client",
            field=models.BooleanField(
                default=False,
                help_text="Unchecked are visible for staff only",
                verbose_name="For client",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="event",
            name="modified_by",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="event_modified_by",
                verbose_name="Modified by",
                to=settings.AUTH_USER_MODEL,
                null=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="event",
            name="modified_on",
            field=models.DateTimeField(
                auto_now=True, verbose_name="Modified on", null=True
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="event",
            name="text",
            field=models.CharField(max_length=150, verbose_name="Subject"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="event",
            name="time",
            field=models.DateTimeField(verbose_name="Time"),
            preserve_default=True,
        ),
    ]
