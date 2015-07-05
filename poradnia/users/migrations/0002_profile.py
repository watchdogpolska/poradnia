# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('user', models.OneToOneField(primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('www', models.URLField(verbose_name='Homepage')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
