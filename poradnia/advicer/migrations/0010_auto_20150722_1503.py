# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('advicer', '0009_attachment'),
    ]

    operations = [
        migrations.RenameField(
            model_name='attachment',
            old_name='letter',
            new_name='advice',
        ),
    ]
