# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('letters', '0002_auto_20150101_0649'),
    ]

    operations = [
        migrations.AddField(
            model_name='letter',
            name='name',
            field=models.CharField(default='Example title', max_length=250),
            preserve_default=False,
        ),
    ]
