# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_auto_20150321_2014'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='high',
        ),
        migrations.AlterField(
            model_name='alarm',
            name='event',
            field=models.OneToOneField(to='events.Event'),
            preserve_default=True,
        ),
    ]
