
import sorl.thumbnail.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0005_auto_20150712_1524'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='picture',
            field=sorl.thumbnail.fields.ImageField(upload_to=b'avatars', null=True, verbose_name='Avatar', blank=True),
            preserve_default=True,
        ),
    ]
