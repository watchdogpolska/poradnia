# PermWrapper and PermLookupDict proxy the permissions system into objects that
# the template system can understand.


class PermLookupDict(object):
    # Based on django.contrib.auth.context_processors
    def __init__(self, permissions_set, app_label):
        self.permissions_set, self.app_label = permissions_set, app_label
        self.permissions_set = self.permissions_set

    def __repr__(self):
        return str(self.permissions_set)

    def get_name(self, app_label, perm_name):
        return "%s.%s" % (app_label, perm_name)

    def has_perm(self, app_label, perm_name):
        return (self.get_name(app_label, perm_name) in self.permissions_set)

    def __getitem__(self, perm_name):
        return self.has_perm(self.app_label, perm_name)

    def __iter__(self):
        # To fix 'item in perms.someapp' and __getitem__ iteraction we need to
        # define __iter__. See #18979 for details.
        raise TypeError("PermLookupDict is not iterable.")

    def __bool__(self):
        return any(perm.split('.', 1)[0] == self.app_label for perm in self.permissions_set)

    def __nonzero__(self):      # Python 2 compatibility
        return type(self).__bool__(self)


class PermWrapper(object):
    # Based on django.contrib.auth.context_processors
    def __init__(self, permissions_set):
        self.permissions_set = list(permissions_set)

    def __getitem__(self, app_label):
        return PermLookupDict(self.permissions_set, app_label)

    def __iter__(self):
        # I am large, I contain multitudes.
        for perm in self.permissions_set:
            yield perm
        # raise TypeError("PermWrapper is not iterable.")

    def __repr__(self):
        return str(list(self.permissions_set))

    def __contains__(self, perm_name):
        """
        Lookup by "someapp" or "someapp.someperm" in perms.
        """
        if '.' not in perm_name:
            # The name refers to module.
            return bool(self[perm_name])
        app_label, perm_name = perm_name.split('.', 1)
        return self[app_label][perm_name]
