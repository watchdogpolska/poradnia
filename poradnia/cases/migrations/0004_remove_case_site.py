# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0003_case_site'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='case',
            name='site',
        ),
    ]
