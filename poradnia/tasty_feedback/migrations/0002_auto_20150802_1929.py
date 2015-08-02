# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('tasty_feedback', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedback',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, help_text='Author', null=True),
            preserve_default=True,
        ),
    ]
