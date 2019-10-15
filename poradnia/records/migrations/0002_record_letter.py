
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('letters', '0001_initial'),
        ('records', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='record',
            name='letter',
            field=models.ForeignKey(blank=True, to='letters.Letter', null=True),
            preserve_default=True,
        ),
    ]
