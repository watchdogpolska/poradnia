
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0017_case_deadline'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='case',
            options={'ordering': ['last_send'], 'permissions': (('can_view_all', 'Can view all cases'), ('can_view', 'Can view'), ('can_view_free', 'Can view free cases'), ('can_select_client', 'Can select client'), ('can_assign', 'Can assign new permissions'), ('can_send_to_client', 'Can send text to client'), ('can_manage_permission', 'Can assign permission'), ('can_add_record', 'Can add record'), ('can_change_own_record', 'Can change own records'), ('can_change_all_record', 'Can change all records'))},
        ),
        migrations.AlterField(
            model_name='case',
            name='client',
            field=models.ForeignKey(related_name='case_client',on_delete=models.CASCADE, verbose_name='Client', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='case',
            name='created_by',
            field=models.ForeignKey(related_name='case_created', on_delete=models.CASCADE, verbose_name='Created by', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='case',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created on'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='case',
            name='deadline',
            field=models.ForeignKey(related_name='event_deadline', on_delete=models.CASCADE, verbose_name='Dead-line', blank=True, to='events.Event', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='case',
            name='last_action',
            field=models.DateTimeField(null=True, verbose_name='Last action', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='case',
            name='last_send',
            field=models.DateTimeField(null=True, verbose_name='Last send', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='case',
            name='letter_count',
            field=models.IntegerField(default=0, verbose_name='Letter count'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='case',
            name='modified_by',
            field=models.ForeignKey(related_name='case_modified', on_delete=models.CASCADE, verbose_name='Modified by', to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='case',
            name='modified_on',
            field=models.DateTimeField(auto_now=True, verbose_name='Modified on', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='case',
            name='name',
            field=models.CharField(max_length=150, verbose_name='Subject'),
            preserve_default=True,
        ),
    ]
