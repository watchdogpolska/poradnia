from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("cases", "0028_auto_20151218_0036")]

    operations = [
        migrations.AddField(
            model_name="case",
            name="has_project",
            field=models.BooleanField(default=False, verbose_name="Has project"),
        )
    ]
