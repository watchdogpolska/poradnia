# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0014_auto_20150312_2338'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='modified_by',
            field=models.ForeignKey(related_name='case_modified', to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
