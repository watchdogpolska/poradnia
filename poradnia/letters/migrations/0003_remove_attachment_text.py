# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('letters', '0002_letter_case'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attachment',
            name='text',
        ),
    ]
