# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0019_auto_20150503_1741'),
        ('advicer', '0004_auto_20150503_1741'),
    ]

    operations = [
        migrations.AddField(
            model_name='advice',
            name='case',
            field=models.ForeignKey(blank=True, to='cases.Case', null=True),
            preserve_default=True,
        ),
    ]
