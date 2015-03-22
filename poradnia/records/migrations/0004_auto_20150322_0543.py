# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0004_auto_20150322_0543'),
        ('records', '0003_auto_20150321_1246'),
    ]

    operations = [
        migrations.AddField(
            model_name='record',
            name='alarm',
            field=models.OneToOneField(null=True, blank=True, to='events.Alarm'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='record',
            name='event',
            field=models.OneToOneField(null=True, blank=True, to='events.Event'),
            preserve_default=True,
        ),
    ]
