# Generated by Django 3.2.18 on 2023-02-16 15:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0023_auto_20220103_1354"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="first_name",
            field=models.CharField(
                blank=True, max_length=150, verbose_name="first name"
            ),
        ),
    ]
