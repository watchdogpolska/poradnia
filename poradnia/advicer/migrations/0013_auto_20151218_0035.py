# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('advicer', '0012_auto_20151124_1541'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advice',
            name='grant_on',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Grant on'),
        ),
    ]
