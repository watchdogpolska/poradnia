# Generated by Django 1.11.8 on 2018-04-15 17:22
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("events", "0008_auto_20180415_1916")]

    operations = [
        migrations.AlterField(
            model_name="reminder",
            name="event",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="events.Event"
            ),
        )
    ]
