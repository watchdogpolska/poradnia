from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("keys", "0002_auto_20150710_2133")]

    operations = [
        migrations.AlterUniqueTogether(
            name="key", unique_together={("user", "password")}
        )
    ]
