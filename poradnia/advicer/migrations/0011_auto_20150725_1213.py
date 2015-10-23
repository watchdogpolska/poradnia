# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advicer', '0010_auto_20150722_1503'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='advice',
            options={'ordering': ['created_on'], 'verbose_name': 'Advice', 'verbose_name_plural': 'Advices', 'permissions': (('can_view_all_advices', 'Can view all advices'),)},
        ),
        migrations.AlterModelOptions(
            name='area',
            options={'verbose_name': 'Area', 'verbose_name_plural': 'Areas'},
        ),
        migrations.AlterModelOptions(
            name='institutionkind',
            options={'verbose_name': 'Institution kind', 'verbose_name_plural': 'Institution kinds'},
        ),
        migrations.AlterModelOptions(
            name='issue',
            options={'verbose_name': 'Issue', 'verbose_name_plural': 'Issues'},
        ),
        migrations.AlterModelOptions(
            name='personkind',
            options={'verbose_name': 'Person kind', 'verbose_name_plural': 'Person kinds'},
        ),
        migrations.AlterField(
            model_name='advice',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Creation date'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='advice',
            name='modified_on',
            field=models.DateTimeField(auto_now=True, verbose_name='Modification date', null=True),
            preserve_default=True,
        ),
    ]
