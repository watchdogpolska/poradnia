# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def update_site_forward(apps, schema_editor):
    """Set site domain and name."""
    Group = apps.get_model('auth', 'Group')
    LocalGroup = apps.get_model("permissions", "LocalGroup")
    for rank in ('client', 'lawyer', 'student', 'secretary', 'spectator'):
        LocalGroup.objects.update_or_create(
            rank=rank,
            group=Group.objects.get_or_create(name=rank)[0],
        )


class Migration(migrations.Migration):

    dependencies = [
        ('permissions', '0003_auto_20150104_2110'),
    ]

    operations = [
        migrations.RunPython(update_site_forward),
    ]
