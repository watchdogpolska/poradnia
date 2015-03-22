# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0002_record_letter'),
    ]

    operations = [
        migrations.AlterField(
            model_name='record',
            name='letter',
            field=models.OneToOneField(null=True, blank=True, to='letters.Letter'),
            preserve_default=True,
        ),
    ]
