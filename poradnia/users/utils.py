from django.core.exceptions import PermissionDenied
from guardian.shortcuts import get_perms


def has_perms(user, perms, obj=None,  required_all=True):
    if obj:
        perms_obj = get_perms(user, obj)
        tests = [perm in perms_obj for perm in perms]
    else:
        tests = [user.has_perm(perm) for perm in perms]
    if required_all and all(tests):
        return True
    if not required_all and any(tests):
        return True
    raise PermissionDenied

