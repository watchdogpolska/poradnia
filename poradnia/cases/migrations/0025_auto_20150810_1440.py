
import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0024_auto_20150809_2148'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='status',
            field=model_utils.fields.StatusField(default=b'0', max_length=100, no_check_for_status=True, choices=[(0, 'dummy')]),
            preserve_default=True,
        ),
    ]
