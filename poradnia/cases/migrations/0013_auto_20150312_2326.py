from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("cases", "0012_auto_20150311_0434")]

    operations = [
        migrations.RemoveField(model_name="case", name="created_by"),
        migrations.RemoveField(model_name="case", name="created_on"),
        migrations.RemoveField(model_name="case", name="modified_by"),
        migrations.RemoveField(model_name="case", name="modified_on"),
    ]
