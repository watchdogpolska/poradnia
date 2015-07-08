# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20150705_1242'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profile',
            options={'verbose_name': 'Profile', 'verbose_name_plural': 'Profiles'},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'Profile', 'verbose_name_plural': 'Profiles', 'permissions': (('can_view_other', 'Can view other'),)},
        ),
    ]
