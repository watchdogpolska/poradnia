from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("cases", "0016_auto_20150316_0931"), ("letters", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="letter",
            name="case",
            field=models.ForeignKey(
                on_delete=models.CASCADE, default=1, to="cases.Case"
            ),
            preserve_default=False,
        )
    ]
