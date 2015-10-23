# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0016_auto_20150316_0931'),
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='alarm',
            name='case',
            field=models.ForeignKey(default=1, to='cases.Case'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='case',
            field=models.ForeignKey(default=1, to='cases.Case'),
            preserve_default=False,
        ),
    ]
