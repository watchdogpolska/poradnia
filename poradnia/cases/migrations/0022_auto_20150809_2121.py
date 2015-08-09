# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import model_utils.fields



class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0021_initial_permission_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='status',
            field=model_utils.fields.StatusField(default=b'A', max_length=100, no_check_for_status=True, choices=[(0, 'dummy')]),
            preserve_default=True,
        ),
    ]
