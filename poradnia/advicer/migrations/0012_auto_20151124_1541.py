# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('advicer', '0011_auto_20150725_1213'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advice',
            name='issues',
            field=models.ManyToManyField(to='advicer.Issue', verbose_name='Issues', blank=True),
            preserve_default=True,
        ),
    ]
