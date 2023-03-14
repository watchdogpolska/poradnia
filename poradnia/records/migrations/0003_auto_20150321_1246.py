from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("records", "0002_record_letter")]

    operations = [
        migrations.AlterField(
            model_name="record",
            name="letter",
            field=models.OneToOneField(
                on_delete=models.CASCADE, null=True, blank=True, to="letters.Letter"
            ),
            preserve_default=True,
        )
    ]
