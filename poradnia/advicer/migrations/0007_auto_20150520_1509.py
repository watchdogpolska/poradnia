# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('advicer', '0006_auto_20150514_0226'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advice',
            name='case',
            field=models.OneToOneField(null=True, blank=True, to='cases.Case', verbose_name='Case'),
            preserve_default=True,
        ),
    ]
