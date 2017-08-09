from braces.views import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import View
from guardian.shortcuts import get_perms


def has_perms(user, perms, obj=None, required_all=True):
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


class PermissionMixin(LoginRequiredMixin, View):
    def get_queryset(self, *args, **kwargs):
        qs = super(PermissionMixin, self).get_queryset(*args, **kwargs)
        return qs.for_user(self.request.user)
