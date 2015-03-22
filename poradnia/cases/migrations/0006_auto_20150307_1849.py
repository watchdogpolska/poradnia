# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0005_auto_20150305_0755'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='case',
            options={'permissions': (('can_view_all', 'Can view all cases'), ('can_view', 'Can view'), ('can_select_client', 'Can select client'), ('can_assign', 'Can assign new permissions'), ('can_send_to_client', 'Can send text to client'))},
        ),
        migrations.AddField(
            model_name='case',
            name='last_action',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 8, 2, 49, 55, 496358, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='case',
            name='letter_count',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
    ]
