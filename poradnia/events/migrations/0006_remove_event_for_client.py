# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0005_auto_20150503_1741'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='for_client',
        ),
    ]
