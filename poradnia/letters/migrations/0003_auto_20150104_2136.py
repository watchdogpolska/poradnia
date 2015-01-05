# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0003_auto_20150104_2110'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('letters', '0002_auto_20150102_1532'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttachmentComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AttachmentLetter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attachment', models.FileField(upload_to=b'letters/%Y/%m/%d')),
                ('text', models.CharField(max_length=150)),
                ('related', models.ForeignKey(to='letters.Letter')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('record_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='records.Record')),
                ('text', models.TextField(null=True, blank=True)),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=('records.record',),
        ),
        migrations.RemoveField(
            model_name='attachment',
            name='letter',
        ),
        migrations.DeleteModel(
            name='Attachment',
        ),
        migrations.AddField(
            model_name='attachmentcomment',
            name='related',
            field=models.ForeignKey(to='letters.Comment'),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='letter',
            name='comment',
        ),
        migrations.AddField(
            model_name='letter',
            name='accept',
            field=model_utils.fields.MonitorField(default=django.utils.timezone.now, when=set([b'done']), monitor=b'status'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='letter',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='letter',
            name='status',
            field=model_utils.fields.StatusField(default=b'staff', max_length=100, no_check_for_status=True, choices=[(0, 'dummy')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='letter',
            name='text',
            field=models.TextField(),
            preserve_default=True,
        ),
    ]
