
import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('letters', '0006_auto_20150810_1440'),
    ]

    operations = [
        migrations.AlterField(
            model_name='letter',
            name='status',
            field=model_utils.fields.StatusField(default=b'staff', max_length=100, db_index=True, no_check_for_status=True, choices=[(0, 'dummy')]),
            preserve_default=True,
        ),
    ]
