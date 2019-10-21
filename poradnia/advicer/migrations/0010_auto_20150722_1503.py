from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("advicer", "0009_attachment")]

    operations = [
        migrations.RenameField(
            model_name="attachment", old_name="letter", new_name="advice"
        )
    ]
