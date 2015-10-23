# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('cases', '0019_auto_20150503_1741'),
    ]

    operations = [
        migrations.CreateModel(
            name='PermissionGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=25, verbose_name='Name')),
                ('permissions', models.ManyToManyField(to='auth.Permission', verbose_name='Permissions')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
