# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0006_auto_20150307_1849'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='case',
            options={'ordering': ['last_action'], 'permissions': (('can_view_all', 'Can view all cases'), ('can_view', 'Can view'), ('can_select_client', 'Can select client'), ('can_assign', 'Can assign new permissions'), ('can_send_to_client', 'Can send text to client'))},
        ),
        migrations.AlterField(
            model_name='case',
            name='last_action',
            field=models.DateTimeField(),
            preserve_default=True,
        ),
    ]
