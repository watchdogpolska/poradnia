
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('user', models.OneToOneField(primary_key=True, serialize=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('www', models.URLField(verbose_name='Homepage')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
