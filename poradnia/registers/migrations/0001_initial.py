# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Advice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subject', models.CharField(max_length=50, null=True, blank=True)),
                ('grant_on', models.DateTimeField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('visible', models.BooleanField(default=True)),
                ('comment', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InstitutionKind',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Issue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PersonKind',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='advice',
            name='area',
            field=models.ForeignKey(blank=True, to='registers.Area', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='advice',
            name='created_by',
            field=models.ForeignKey(related_name='advice_created_by', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='advice',
            name='institution_kind',
            field=models.ForeignKey(blank=True, to='registers.InstitutionKind', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='advice',
            name='issues',
            field=models.ManyToManyField(to='registers.Issue', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='advice',
            name='modified_by',
            field=models.ForeignKey(related_name='advice_modified_by', to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='advice',
            name='person_kind',
            field=models.ForeignKey(blank=True, to='registers.PersonKind', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='advice',
            name='who',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
