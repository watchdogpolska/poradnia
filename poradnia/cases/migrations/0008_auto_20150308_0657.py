# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0007_auto_20150307_1854'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='case',
            options={'ordering': ['last_action'], 'permissions': (('can_view_all', 'Can view all cases'), ('can_view', 'Can view'), ('can_select_client', 'Can select client'), ('can_assign', 'Can assign new permissions'), ('can_send_to_client', 'Can send text to client'), ('can_manage_permission', 'Can assign permission'), ('can_change_own_record', 'Can change own records'), ('can_change_all_record', 'Can change all records'))},
        ),
    ]
