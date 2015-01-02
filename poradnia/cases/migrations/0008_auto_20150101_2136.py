# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0007_auto_20150101_1632'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitegroup',
            name='rank',
            field=models.CharField(default=b'client', max_length=15, choices=[(b'client', b'client'), (b'lawyer', b'lawyer'), (b'student', b'student'), (b'secretary', b'secretary'), (b'spectator', b'spectator')]),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='permission',
            unique_together=set([('user', 'case')]),
        ),
    ]
