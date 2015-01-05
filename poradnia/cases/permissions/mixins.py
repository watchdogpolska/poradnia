from .utils import PermWrapper


class PermissionGroupContextMixin(object):
    def get_permissions_set(self):
        return self.object.get_permissions_set(self.request.user)

    def get_context_data(self, **kwargs):
        permissions_set = self.get_permissions_set()
        kwargs['perm_case'] = PermWrapper(permissions_set)
        return super(PermissionGroupContextMixin, self).get_context_data(**kwargs)


class PermissionGroupQuerySetMixin(object):
    def get_queryset(self, *args, **kwargs):
        queryset = super(PermissionGroupQuerySetMixin, self).get_queryset(*args, **kwargs)
        return queryset.for_user(self.request.user)


class PermissionGroupMixin(PermissionGroupContextMixin, PermissionGroupQuerySetMixin):
    pass
