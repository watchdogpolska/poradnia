# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import django
from django.db import migrations
import django.contrib.sites.models


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
