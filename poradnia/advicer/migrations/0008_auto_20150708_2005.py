from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("advicer", "0007_auto_20150520_1509")]

    operations = [
        migrations.AlterField(
            model_name="advice",
            name="comment",
            field=models.TextField(null=True, verbose_name="Comment", blank=True),
            preserve_default=True,
        )
    ]
