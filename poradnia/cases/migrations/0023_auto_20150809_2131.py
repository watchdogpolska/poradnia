import model_utils.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("cases", "0022_auto_20150809_2121")]

    operations = [
        migrations.AlterField(
            model_name="case",
            name="status",
            field=model_utils.fields.StatusField(
                default=0,
                max_length=100,
                no_check_for_status=True,
                choices=[(0, "dummy")],
            ),
            preserve_default=True,
        )
    ]
