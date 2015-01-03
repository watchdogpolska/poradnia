# PermWrapper and PermLookupDict proxy the permissions system into objects that
# the template system can understand.


class PermLookupDict(object):
    # Based on django.contrib.auth.context_processors
    def __init__(self, group, app_label):
        self.group, self.app_label = group, app_label
        self.permissions = self.group.permissions.all()

    def __repr__(self):
        return str(self.permissions)

    def has_perm(self, app_label, perm_name):
        return (True if [g for g in self.group.permissions.all()
            if g.content_type.app_label == app_label and
            g.codename == perm_name] else False)

    def __getitem__(self, perm_name):
        return self.has_perm(self.app_label, perm_name)

    def __iter__(self):
        # To fix 'item in perms.someapp' and __getitem__ iteraction we need to
        # define __iter__. See #18979 for details.
        raise TypeError("PermLookupDict is not iterable.")

    def __bool__(self):
        return (True if [g for g in self.group.permissions.all()
            if g.content_type.app_label == self.app_label] else False)

    def __nonzero__(self):      # Python 2 compatibility
        return type(self).__bool__(self)


class PermWrapper(object):
    # Based on django.contrib.auth.context_processors
    def __init__(self, group):
        self.group = group

    def __getitem__(self, app_label):
        return PermLookupDict(self.group, app_label)

    def __iter__(self):
        # I am large, I contain multitudes.
        raise TypeError("PermWrapper is not iterable.")

    def __contains__(self, perm_name):
        """
        Lookup by "someapp" or "someapp.someperm" in perms.
        """
        if '.' not in perm_name:
            # The name refers to module.
            return bool(self[perm_name])
        app_label, perm_name = perm_name.split('.', 1)
        return self[app_label][perm_name]


class PermissionGroupContextMixin(object):
    def get_permission_group(self):
        if hasattr(self, 'object') and hasattr(self.object, 'get_permission_group'):
            return self.object.get_permission_group(self.request.user)
        return None

    def get_context_data(self, **kwargs):
        group = self.get_permission_group()
        kwargs['perm_case'] = PermWrapper(group)
        return super(PermissionGroupContextMixin, self).get_context_data(**kwargs)


class PermissionGroupQuerySetMixin(object):
    def get_queryset(self, *args, **kwargs):
        queryset = super(PermissionGroupQuerySetMixin, self).get_queryset(*args, **kwargs)
        return queryset.for_user(self.request.user)


class PermissionGroupMixin(PermissionGroupContextMixin, PermissionGroupQuerySetMixin):
    pass
