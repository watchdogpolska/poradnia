# Generated by Django 1.10.6 on 2017-03-17 18:27
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("cases", "0030_case_close_perm")]

    operations = [
        migrations.AlterField(
            model_name="case",
            name="id",
            field=models.AutoField(
                primary_key=True, serialize=False, verbose_name="Numer sprawy"
            ),
        )
    ]
