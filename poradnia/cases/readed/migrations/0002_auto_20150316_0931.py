# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('readed', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='readed',
            unique_together=set([('user', 'case')]),
        ),
    ]
