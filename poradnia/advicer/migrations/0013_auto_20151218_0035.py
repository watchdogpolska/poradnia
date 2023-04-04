import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("advicer", "0012_auto_20151124_1541")]

    operations = [
        migrations.AlterField(
            model_name="advice",
            name="grant_on",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="Grant on"
            ),
        )
    ]
