
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_auto_20151108_0017'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='codename',
            field=models.CharField(max_length=15, null=True, verbose_name='Codename', blank=True),
            preserve_default=True,
        ),
    ]
