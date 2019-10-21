from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("letters", "0004_auto_20150503_1741")]

    operations = [
        migrations.AlterField(
            model_name="attachment",
            name="attachment",
            field=models.FileField(upload_to=b"letters/%Y/%m/%d", verbose_name="File"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="letter",
            name="text",
            field=models.TextField(verbose_name="Text"),
            preserve_default=True,
        ),
    ]
