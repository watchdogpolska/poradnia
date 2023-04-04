from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tasty_feedback", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="feedback",
            name="user",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                to=settings.AUTH_USER_MODEL,
                help_text="Author",
                null=True,
            ),
            preserve_default=True,
        )
    ]
