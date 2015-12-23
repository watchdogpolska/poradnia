# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def migrate_last_received(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Letter = apps.get_model("letters", "Letter")
    Case = apps.get_model('cases', "Case")
    for case in Case.objects.all():
        try:
            obj = Letter.objects.filter(case=case).filter(created_by__is_staff=False).order_by('-created_on', '-id').all()[0]
            case.last_received = obj.created_on
            case.save()
        except IndexError:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0026_case_handled'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='last_received',
            field=models.DateTimeField(null=True, verbose_name='Last received', blank=True),
            preserve_default=True,
        ),
        migrations.RunPython(migrate_last_received),
    ]
