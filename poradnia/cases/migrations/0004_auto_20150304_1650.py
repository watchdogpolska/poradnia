import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cases", "0003_auto_20150103_0643")]

    operations = [
        migrations.AlterModelOptions(
            name="case",
            options={
                "permissions": (
                    ("can_view_all", "Can view all cases"),
                    ("can_view", "Can view"),
                )
            },
        ),
        migrations.AlterField(
            model_name="case",
            name="status",
            field=model_utils.fields.StatusField(
                default=b"free",
                max_length=100,
                no_check_for_status=True,
                choices=[(0, "dummy")],
            ),
            preserve_default=True,
        ),
    ]
