from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("records", "0005_auto_20150426_1426")]

    operations = [
        migrations.AlterModelOptions(
            name="record",
            options={
                "ordering": ["created_on", "id"],
                "verbose_name": "Record",
                "verbose_name_plural": "Records",
            },
        )
    ]
