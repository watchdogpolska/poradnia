
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0004_auto_20150322_0543'),
        ('cases', '0016_auto_20150316_0931'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='deadline',
            field=models.ForeignKey(related_name='event_deadline', blank=True, to='events.Event', null=True),
            preserve_default=True,
        ),
    ]
