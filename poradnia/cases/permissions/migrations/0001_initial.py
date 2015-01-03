# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LocalGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rank', models.CharField(default=b'client', max_length=15, choices=[(b'client', b'client'), (b'lawyer', b'lawyer'), (b'student', b'student'), (b'secretary', b'secretary'), (b'spectator', b'spectator')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('case', models.ForeignKey(to='cases.Case')),
                ('group', models.ForeignKey(to='permissions.LocalGroup')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
