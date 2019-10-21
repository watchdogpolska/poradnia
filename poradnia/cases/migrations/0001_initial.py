
import django.utils.timezone
import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Case',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=150)),
                ('status', model_utils.fields.StatusField(default=b'open', max_length=100, no_check_for_status=True, choices=[(b'open', b'open'), (b'closed', b'closed')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, monitor=b'status')),
            ],
            options={
                'permissions': (('can_select_client', 'Can select client'), ('can_view_all', 'Can view all cases')),
            },
            bases=(models.Model,),
        ),
    ]
