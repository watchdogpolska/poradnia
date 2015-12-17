# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0027_case_last_received'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='tags',
            field=models.ManyToManyField(to='tags.Tag', verbose_name='Tags', blank=True),
        ),
    ]
