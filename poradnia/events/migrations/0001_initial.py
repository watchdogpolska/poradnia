# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Alarm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('deadline', models.BooleanField(default=False)),
                ('time', models.DateTimeField()),
                ('for_user', models.BooleanField(default=False)),
                ('high', models.BooleanField(default=False)),
                ('text', models.CharField(max_length=150)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('created_by', models.ForeignKey(related_name='event_created_by', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(related_name='event_modified_by', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='alarm',
            name='event',
            field=models.ForeignKey(to='events.Event'),
            preserve_default=True,
        ),
    ]
