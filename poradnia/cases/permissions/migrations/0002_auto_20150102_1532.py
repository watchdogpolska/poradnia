# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('permissions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='permission',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='permission',
            unique_together=set([('user', 'case')]),
        ),
        migrations.AddField(
            model_name='localgroup',
            name='group',
            field=models.ForeignKey(to='auth.Group'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='localgroup',
            unique_together=set([('rank', 'group')]),
        ),
    ]
