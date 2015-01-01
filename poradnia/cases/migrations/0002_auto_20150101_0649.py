# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='case',
            options={'permissions': (('can_select_client', 'Can select client'),)},
        ),
        migrations.AlterField(
            model_name='case',
            name='tags',
            field=models.ManyToManyField(to='cases.Tag', null=True, blank=True),
            preserve_default=True,
        ),
    ]
