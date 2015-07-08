# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('advicer', '0002_auto_20150325_1857'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='advice',
            options={'ordering': ['created_on'], 'permissions': (('can_view_all_advices', 'Can view all advices'),)},
        ),
    ]
