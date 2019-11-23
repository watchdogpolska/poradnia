from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("users", "0004_auto_20150708_2005")]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={
                "verbose_name": "User",
                "verbose_name_plural": "Users",
                "permissions": (("can_view_other", "Can view other"),),
            },
        )
    ]
