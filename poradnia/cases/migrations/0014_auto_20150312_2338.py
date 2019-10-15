
import datetime

from django.conf import settings
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cases', '0013_auto_20150312_2326'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='created_by',
            field=models.ForeignKey(related_name='case_created',on_delete=models.CASCADE, default=1, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='case',
            name='created_on',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 13, 6, 38, 41, 77810, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='case',
            name='modified_by',
            field=models.ForeignKey(related_name='case_modified', on_delete=models.CASCADE,default=1, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='case',
            name='modified_on',
            field=models.DateTimeField(auto_now=True, null=True),
            preserve_default=True,
        ),
    ]
