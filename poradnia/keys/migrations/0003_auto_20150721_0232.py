# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('keys', '0002_auto_20150710_2133'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='key',
            unique_together=set([('user', 'password')]),
        ),
    ]
