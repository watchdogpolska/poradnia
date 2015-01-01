# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0004_remove_case_site'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='case',
            options={'permissions': (('can_select_client', 'Can select client'), ('can_view_all', 'Can view all cases'))},
        ),
    ]
