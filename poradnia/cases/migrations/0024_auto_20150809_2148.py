# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db.models import Count

from django.db import models, migrations


def delete_empty(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Case = apps.get_model("cases", "Case")
    Case.objects.annotate(record_count=Count('record')).filter(record_count=0).update(status=Case.STATUS.closed)


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0023_auto_20150809_2131'),
    ]

    operations = [
        migrations.RunPython(delete_empty)
    ]
