from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("letters", "0002_letter_case")]

    operations = [migrations.RemoveField(model_name="attachment", name="text")]
