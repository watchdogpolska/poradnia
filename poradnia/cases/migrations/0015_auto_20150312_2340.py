
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0014_auto_20150312_2338'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='modified_by',
            field=models.ForeignKey(related_name='case_modified', to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
