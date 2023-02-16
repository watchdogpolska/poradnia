from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("letters", "0005_auto_20150708_2005")]

    operations = [
        migrations.AlterModelOptions(
            name="letter",
            options={
                "ordering": ["-created_on"],
                "verbose_name": "Letter",
                "verbose_name_plural": "Letters",
            },
        )
    ]
