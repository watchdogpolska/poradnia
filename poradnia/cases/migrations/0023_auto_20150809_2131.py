# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import model_utils.fields


def update_status(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Case = apps.get_model("cases", "Case")
    db_alias = schema_editor.connection.alias
    Case.objects.using(db_alias).filter(status='A').update(status=0)
    Case.objects.using(db_alias).filter(status='B').update(status=1)
    Case.objects.using(db_alias).filter(status='C').update(status=2)


def update_status_back(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Case = apps.get_model("cases", "Case")
    db_alias = schema_editor.connection.alias
    Case.objects.using(db_alias).filter(status=0).update(status='A')
    Case.objects.using(db_alias).filter(status=1).update(status='B')
    Case.objects.using(db_alias).filter(status=2).update(status='C')


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0022_auto_20150809_2121'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='status',
            field=model_utils.fields.StatusField(default=0, max_length=100, no_check_for_status=True, choices=[(0, 'dummy')]),
            preserve_default=True,
        ),
        migrations.RunPython(update_status, update_status_back)

    ]
