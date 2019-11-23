from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("events", "0002_auto_20150321_1246")]

    operations = [
        migrations.RenameField(
            model_name="event", old_name="for_user", new_name="for_client"
        )
    ]
