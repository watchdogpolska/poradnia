
from django.conf import settings
from django.db import migrations, models

if 'avatar' in settings.INSTALLED_APPS:
    def migrate_avatar(apps, schema_editor):
        Avatar = apps.get_model("avatar", "Avatar")
        for avatar in Avatar.objects.filter(primary=True).all():
            avatar.user.picture = avatar.avatar
            avatar.user.save()
            avatar.save()

    class Migration(migrations.Migration):
        dependencies = [
            ('users', '0006_user_picture'),
            ('avatar', '0001_initial')
        ]

        operations = [
            migrations.RunPython(migrate_avatar)

        ]
else:
    class Migration(migrations.Migration):
        dependencies = [('users', '0006_user_picture'), ]
        operations = []
