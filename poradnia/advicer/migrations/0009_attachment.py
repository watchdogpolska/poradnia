# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advicer', '0008_auto_20150708_2005'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attachment', models.FileField(upload_to=b'letters/%Y/%m/%d', verbose_name='File')),
                ('letter', models.ForeignKey(to='advicer.Advice')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Attachment',
                'verbose_name_plural': 'Attachments',
            },
            bases=(models.Model,),
        ),
    ]
