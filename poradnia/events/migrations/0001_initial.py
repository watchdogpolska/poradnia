# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alarm',
            fields=[
                ('record_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='records.Record')),
            ],
            options={
            },
            bases=('records.record',),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('record_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='records.Record')),
                ('deadline', models.BooleanField(default=False)),
                ('time', models.DateTimeField()),
                ('text', models.CharField(max_length=150)),
            ],
            options={
            },
            bases=('records.record',),
        ),
        migrations.AddField(
            model_name='alarm',
            name='event',
            field=models.ForeignKey(to='events.Event'),
            preserve_default=True,
        ),
    ]
