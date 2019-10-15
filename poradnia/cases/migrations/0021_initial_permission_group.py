
from django.db import migrations

PERM_INITIAL = {'wsparcie': ('can_add_record',
                             'can_change_own_record',
                             'can_view',
                            'can_view_all'
                             ),
                'obserwator': (
                            'can_view',
                            'can_view_all'),
                'klient': ('can_add_record',
                           'can_send_to_client',
                           'can_view'),
                'admin': '__all__',
                }


def get_perm(p, codenames=None):
    qs = p.objects.filter(**{'content_type__app_label': 'cases', 'content_type__model': 'case'})
    if codenames is not '__all__':
        qs = qs.filter(codename__in=codenames)
    return qs.all()


def add_groups(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    PermissionGroup = apps.get_model("cases", "PermissionGroup")
    Permission = apps.get_model('auth', 'Permission')
    for name, codenames in PERM_INITIAL.items():
        p, _ = PermissionGroup.objects.get_or_create(name=name)
        p.permissions = get_perm(Permission, codenames)
        p.save()


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('cases', '0020_permissiongroup'),
    ]

    operations = [
            migrations.RunPython(add_groups),
    ]
