# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
import django.contrib.sites.models
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('sites', '0002_set_site_domain_and_name'),
    ]

    if django.VERSION[:2] >= (1, 8):
        operations = [
            migrations.AlterModelManagers(
                name='site',
                managers=[
                    ('objects', django.contrib.sites.models.SiteManager()),
                ],
            ),
        ]
    else:
        operations = [
        ]
