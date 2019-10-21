from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cases", "0001_initial"), ("events", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="alarm",
            name="case",
            field=models.ForeignKey(
                on_delete=models.CASCADE, default=1, to="cases.Case"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="event",
            name="case",
            field=models.ForeignKey(
                on_delete=models.CASCADE, default=1, to="cases.Case"
            ),
            preserve_default=False,
        ),
    ]
