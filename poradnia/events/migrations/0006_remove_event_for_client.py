from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("events", "0005_auto_20150503_1741")]

    operations = [migrations.RemoveField(model_name="event", name="for_client")]
