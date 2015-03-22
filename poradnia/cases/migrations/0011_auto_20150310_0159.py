# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cases', '0010_auto_20150308_0917'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='created_by',
            field=models.ForeignKey(default=1, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='case',
            name='created_on',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 10, 8, 59, 49, 423287, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='case',
            name='client',
            field=models.ForeignKey(related_name='case_client', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
