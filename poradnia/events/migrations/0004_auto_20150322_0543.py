from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("events", "0003_auto_20150321_2014")]

    operations = [
        migrations.RemoveField(model_name="event", name="high"),
        migrations.AlterField(
            model_name="alarm",
            name="event",
            field=models.OneToOneField(on_delete=models.CASCADE, to="events.Event"),
            preserve_default=True,
        ),
    ]
