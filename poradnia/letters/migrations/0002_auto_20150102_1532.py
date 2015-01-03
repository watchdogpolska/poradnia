# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('letters', '0001_initial'),
        ('records', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Letter',
            fields=[
                ('record_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='records.Record')),
                ('status', model_utils.fields.StatusField(default=b'open', max_length=100, no_check_for_status=True, choices=[(b'open', b'open'), (b'closed', b'closed')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, monitor=b'status')),
                ('name', models.CharField(max_length=250)),
                ('text', models.TextField(null=True, blank=True)),
                ('comment', models.TextField(null=True, blank=True)),
            ],
            options={
            },
            bases=('records.record',),
        ),
        migrations.AddField(
            model_name='attachment',
            name='letter',
            field=models.ForeignKey(to='letters.Letter'),
            preserve_default=True,
        ),
    ]
