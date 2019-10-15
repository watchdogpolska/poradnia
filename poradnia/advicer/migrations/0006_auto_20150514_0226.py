
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advicer', '0005_advice_case'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advice',
            name='case',
            field=models.OneToOneField(null=True, blank=True, to='cases.Case'),
            preserve_default=True,
        ),
    ]
