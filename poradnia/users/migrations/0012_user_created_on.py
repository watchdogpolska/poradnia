# Generated by Django 1.9.9 on 2016-10-19 18:56
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("users", "0011_auto_20160409_2334")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="created_on",
            field=models.DateTimeField(
                auto_now_add=True, null=True, verbose_name="Created on"
            ),
        )
    ]
