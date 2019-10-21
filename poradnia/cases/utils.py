from django.contrib.contenttypes.models import ContentType

from poradnia.cases.models import Case
from poradnia.users.models import User


def get_users_with_perm(obj, perm):
    content_type = ContentType.objects.get_for_model(Case)

    return (
        User.objects.filter(
            caseuserobjectpermission__content_object=obj,
            caseuserobjectpermission__permission__codename=perm,
            caseuserobjectpermission__permission__content_type=content_type,
        )
        .distinct()
        .all()
    )
