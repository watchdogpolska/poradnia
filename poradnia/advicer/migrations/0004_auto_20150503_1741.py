from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("advicer", "0003_auto_20150325_1858")]

    operations = [
        migrations.AlterField(
            model_name="area",
            name="name",
            field=models.CharField(max_length=50, verbose_name=b"Name"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="institutionkind",
            name="name",
            field=models.CharField(max_length=50, verbose_name=b"Name"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="issue",
            name="name",
            field=models.CharField(max_length=50, verbose_name=b"Name"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="personkind",
            name="name",
            field=models.CharField(max_length=50, verbose_name=b"Name"),
            preserve_default=True,
        ),
    ]
