# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('letters', '0003_auto_20150104_2136'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attachment', models.FileField(upload_to=b'letters/%Y/%m/%d')),
                ('text', models.CharField(max_length=150)),
                ('letter', models.ForeignKey(to='letters.Letter')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='attachmentcomment',
            name='related',
        ),
        migrations.DeleteModel(
            name='AttachmentComment',
        ),
        migrations.RemoveField(
            model_name='attachmentletter',
            name='related',
        ),
        migrations.DeleteModel(
            name='AttachmentLetter',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='record_ptr',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='user',
        ),
        migrations.DeleteModel(
            name='Comment',
        ),
        migrations.AddField(
            model_name='letter',
            name='genre',
            field=models.CharField(default=b'mail', max_length=20, choices=[(b'mail', b'mail'), (b'comment', b'comment')]),
            preserve_default=True,
        ),
    ]
