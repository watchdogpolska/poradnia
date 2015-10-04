# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0004_auto_20150322_0543'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='record',
            options={'verbose_name': 'Record', 'verbose_name_plural': 'Records'},
        ),
        migrations.AddField(
            model_name='record',
            name='created_on',
            field=models.DateTimeField(default=datetime.datetime(2015, 4, 26, 21, 26, 57, 237045, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
