# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0002_record_created_by'),
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('record_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='records.Record')),
                ('text', models.TextField()),
            ],
            options={
            },
            bases=('records.record',),
        ),
        migrations.RemoveField(
            model_name='record',
            name='created_by',
        ),
    ]
