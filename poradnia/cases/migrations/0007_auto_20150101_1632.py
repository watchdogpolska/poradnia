# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sites', '0002_set_site_domain_and_name'),
        ('cases', '0006_permission'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rank', models.CharField(default=b'client', max_length=15, choices=[(b'client', b'client'), (b'lawyer', b'lawyer'), (b'student', b'student'), (b'secretary', b'secretary')])),
                ('group', models.ForeignKey(to='auth.Group')),
                ('site', models.ForeignKey(to='sites.Site')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='permission',
            name='user',
            field=models.ForeignKey(default=1, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
