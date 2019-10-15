
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advicer', '0011_auto_20150725_1213'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advice',
            name='issues',
            field=models.ManyToManyField(to='advicer.Issue', verbose_name='Issues', blank=True),
            preserve_default=True,
        ),
    ]
