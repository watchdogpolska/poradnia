# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import sorl.thumbnail.fields


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0005_auto_20150712_1524'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='picture',
            field=sorl.thumbnail.fields.ImageField(upload_to=b'avatars', null=True, verbose_name='Avatar', blank=True),
            preserve_default=True,
        ),
    ]
