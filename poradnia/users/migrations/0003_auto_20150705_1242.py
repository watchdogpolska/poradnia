# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_profile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='www',
            field=models.URLField(null=True, verbose_name='Homepage', blank=True),
            preserve_default=True,
        ),
    ]
