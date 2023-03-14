from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("users", "0007_migrate_avatars")]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={
                "ordering": ["pk"],
                "verbose_name": "User",
                "verbose_name_plural": "Users",
                "permissions": (("can_view_other", "Can view other"),),
            },
        )
    ]
