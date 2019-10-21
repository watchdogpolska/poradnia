from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cases", "0008_auto_20150308_0657")]

    operations = [
        migrations.AlterField(
            model_name="case",
            name="last_action",
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        )
    ]
