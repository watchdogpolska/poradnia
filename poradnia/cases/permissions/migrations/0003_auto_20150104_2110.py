# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('permissions', '0002_auto_20150102_1532'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='permission',
            options={'permissions': (('can_delete_own_permission', 'Can delete own permission'),)},
        ),
    ]
