from django.core.exceptions import ImproperlyConfigured
from guardian.shortcuts import assign_perm

from poradnia.users.factories import UserFactory


class PermissionStatusMixin(object):
    """Mixin to verify object permission status codes for different users
    Require user with username='john' and password='pass'
    Attributes:
        permission (str): Permission name or "superuser"
        status_anonymous (int): Status code for anonymouser
        status_has_permission (int): Status code for user with permission
        status_no_permission (403): Status code for user without permission
        url (str): url to test
    NOTE: based on https://github.com/watchdogpolska/feder/blob/a80d6ea7/feder/main/mixins.py#L113
    """
    url = None
    permissions = None
    status_anonymous = 302
    status_no_permission = 403
    status_has_permission = 200

    def setUp(self):
        super(PermissionStatusMixin, self).setUp()

    def get_url(self):
        """Get url to tests
        Returns:
            str: url to test
        Raises:
            ImproperlyConfigured: Missing a url to test
        """
        if self.url is None:
            raise ImproperlyConfigured(
                '{0} is missing a url to test. Define {0}.url '
                'or override {0}.get_url().'.format(self.__class__.__name__))
        return self.url

    def get_permissions(self):
        """Returns the permission to assign for granted permission user
        Returns:
            list: A list of permission in format ```codename.permission_name```
        Raises:
            ImproperlyConfigured: Missing a permission to assign
        """
        if self.permissions is None:
            raise ImproperlyConfigured(
                '{0} is missing a permissions to assign. Define {0}.permission '
                'or override {0}.get_permission().'.format(self.__class__.__name__))
        return self.permissions[:]

    def make_regular_user(self):
        """Returns a user with no extra permissions"""
        return UserFactory(username="John")

    def make_privileged_user(self):
        """Returns a user with permissions granted"""
        permissions = self.get_permissions()
        if "superuser" in permissions:
            permissions.pop(permissions.index("superuser"))
            user = UserFactory(username="John", is_superuser=True)
        else:
            user = UserFactory(username="John")
        for perm in permissions:
            assign_perm(perm, user)
        return user

    def login(self, user):
        """Login client to user"""
        self.client.login(username=user.username, password='pass')

    def test_status_code_for_anonymous_user(self):
        """A test status code of response for anonymous user"""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, self.status_anonymous)

    def test_status_code_for_signed_user(self):
        """A test for status code of response for signed (logged-in) user"""
        user = self.make_regular_user()
        self.login(user)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, self.status_no_permission)

    def test_status_code_for_privileged_user(self):
        """A test for status code of response for privileged user
        Grant permission to permission-carrying object and login before test
        """
        user = self.make_privileged_user()
        self.login(user)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, self.status_has_permission)
