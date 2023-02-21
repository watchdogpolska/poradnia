from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("letters", "0007_auto_20150817_1707")]

    operations = [
        migrations.AddField(
            model_name="letter",
            name="eml",
            field=models.FileField(
                help_text="Original full content of message",
                upload_to=b"messages",
                null=True,
                verbose_name="Raw message contents",
            ),
            preserve_default=True,
        )
    ]
