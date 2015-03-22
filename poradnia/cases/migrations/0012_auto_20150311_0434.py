# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cases', '0011_auto_20150310_0159'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='modified_by',
            field=models.ForeignKey(related_name='case_modified', default=1, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='case',
            name='modified_on',
            field=models.DateTimeField(auto_now=True, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='case',
            name='created_by',
            field=models.ForeignKey(related_name='case_created', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
