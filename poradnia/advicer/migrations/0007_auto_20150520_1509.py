
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advicer', '0006_auto_20150514_0226'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advice',
            name='case',
            field=models.OneToOneField(on_delete=models.CASCADE,null=True, blank=True, to='cases.Case', verbose_name='Case'),
            preserve_default=True,
        ),
    ]
