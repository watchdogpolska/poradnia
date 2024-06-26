from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("cases", "0018_auto_20150428_0733")]

    operations = [
        migrations.AlterModelOptions(
            name="case",
            options={
                "ordering": ["last_send"],
                "permissions": (
                    ("can_view_all", "Can view all cases"),
                    ("can_view", "Can view"),
                    ("can_select_client", "Can select client"),
                    ("can_assign", "Can assign new permissions"),
                    ("can_send_to_client", "Can send text to client"),
                    ("can_manage_permission", "Can assign permission"),
                    ("can_add_record", "Can add record"),
                    ("can_change_own_record", "Can change own records"),
                    ("can_change_all_record", "Can change all records"),
                ),
            },
        )
    ]
