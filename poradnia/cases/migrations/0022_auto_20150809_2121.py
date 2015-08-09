# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import model_utils.fields


def update_status(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Case = apps.get_model("cases", "Case")
    db_alias = schema_editor.connection.alias
    Case.objects.using(db_alias).filter(status='open').update(status='A')
    Case.objects.using(db_alias).filter(status='assigned').update(status='B')
    Case.objects.using(db_alias).filter(status='closed').update(status='C')


def update_status_back(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Case = apps.get_model("cases", "Case")
    db_alias = schema_editor.connection.alias
    Case.objects.using(db_alias).filter(status='A').update(status='open')
    Case.objects.using(db_alias).filter(status='B').update(status='assigned')
    Case.objects.using(db_alias).filter(status='C').update(status='closed')


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0021_initial_permission_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='status',
            field=model_utils.fields.StatusField(default=b'A', max_length=100, no_check_for_status=True, choices=[(0, 'dummy')]),
            preserve_default=True,
        ),
        migrations.RunPython(update_status, update_status_back)
    ]
