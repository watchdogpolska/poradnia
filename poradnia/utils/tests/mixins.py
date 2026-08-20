from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from guardian.shortcuts import assign_perm


class AssertSendMailMixin:
    @staticmethod
    def _templates_used(email):
        return [
            template
            for template in email.extra_headers["Template"].split("-")
            if email.extra_headers["Template"] and template != "None"
        ]

    def assertMailSend(self, template=None, subject=None, to=None, expected_count=1):
        emails = [
            email
            for email in mail.outbox
            if (not template or template in self._templates_used(email))
            and (not subject or subject in email.subject)
            and (not to or to in email.to)
        ]
        self.assertEqual(
            len(emails),
            expected_count,
            "Invalid number of mail with template {template_name} and subject {subject} was send to {to}.".format(
                template_name=template, subject=subject, to=to
            ),
        )


class AdminTestCaseMixin:
    """Local replacement for the unmaintained atom library's
    AdminTestCaseMixin (see requirements/base.txt)."""

    user_factory_cls = None
    factory_cls = None
    model = None
    changelist_viewname = None
    change_viewname = None
    delete_viewname = None
    history_viewname = None
    QUERY_LIMIT = 30

    def get_changelist_viewname(self):
        if self.changelist_viewname is None and self.model is None:
            raise ImproperlyConfigured(
                "{0} is missing a {0}.changelist_viewname or {0}.model.".format(
                    self.__class__.__name__
                )
            )
        return self.changelist_viewname or "admin:{}_{}_changelist".format(
            self.model._meta.app_label, self.model._meta.model_name
        )

    def get_change_viewname(self):
        if self.change_viewname is None and self.model is None:
            raise ImproperlyConfigured(
                "{0} is missing a {0}.change_viewname or {0}.model.".format(
                    self.__class__.__name__
                )
            )
        return self.change_viewname or "admin:{}_{}_change".format(
            self.model._meta.app_label, self.model._meta.model_name
        )

    def get_delete_viewname(self):
        if self.delete_viewname is None and self.model is None:
            raise ImproperlyConfigured(
                "{0} is missing a {0}.delete_viewname or {0}.model.".format(
                    self.__class__.__name__
                )
            )
        return self.delete_viewname or "admin:{}_{}_delete".format(
            self.model._meta.app_label, self.model._meta.model_name
        )

    def get_history_viewname(self):
        if self.history_viewname is None and self.model is None:
            raise ImproperlyConfigured(
                "{0} is missing a {0}.history_viewname or {0}.model.".format(
                    self.__class__.__name__
                )
            )
        return self.history_viewname or "admin:{}_{}_history".format(
            self.model._meta.app_label, self.model._meta.model_name
        )

    def get_factory_cls(self):
        if self.factory_cls is None:
            raise ImproperlyConfigured(
                "{0} is missing a {0}.factory_cls.".format(self.__class__.__name__)
            )
        return self.factory_cls

    def setUp(self):
        if not hasattr(self, "assertNumQueriesLessThan"):
            self.skipTest(
                "{0} is missing a {0}.assertNumQueriesLessThan method. "
                "Use test_plus.test.TestCase as base class.".format(
                    self.__class__.__name__
                )
            )
        self.object = self.factory_cls()
        self.user = self.user_factory_cls(
            password="password", is_superuser=True, is_staff=True
        )
        self.client.login(username=self.user.username, password="password")

    def test_status_changelist(self):
        url = reverse(self.get_changelist_viewname())
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 200, "Invalid status code on '{}'".format(url)
        )

    def test_status_change_view(self):
        url = reverse(self.get_change_viewname(), args=[self.object.pk])
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 200, "Invalid status code on '{}'".format(url)
        )

    def test_status_delete_view(self):
        url = reverse(self.get_delete_viewname(), args=[self.object.pk])
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 200, "Invalid status code on '{}'".format(url)
        )

    def test_status_history_view(self):
        url = reverse(self.get_history_viewname(), args=[self.object.pk])
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 200, "Invalid status code on '{}'".format(url)
        )

    def test_changelist_queries_limit(self):
        self.factory_cls.create_batch(size=20)
        url = reverse(self.get_changelist_viewname())
        with self.assertNumQueriesLessThan(self.QUERY_LIMIT):
            self.client.get(url)

    def test_change_view_queries_limit(self):
        self.factory_cls.create_batch(size=20)
        url = reverse(self.get_change_viewname(), args=[self.object.pk])
        with self.assertNumQueriesLessThan(self.QUERY_LIMIT):
            self.client.get(url)


class PermissionStatusMixin:
    """Local replacement for the unmaintained atom library's
    PermissionStatusMixin (see requirements/base.txt). Requires a user
    with username='john' and password='pass'."""

    url = None
    permission = None
    status_anonymous = 302
    status_no_permission = 403
    status_has_permission = 200

    def get_url(self):
        if self.url is None:
            raise ImproperlyConfigured(
                "{0} is missing a url to test. Define {0}.url "
                "or override {0}.get_url().".format(self.__class__.__name__)
            )
        return self.url

    def get_permission(self):
        if self.permission is None:
            raise ImproperlyConfigured(
                "{0} is missing a permissions to assign. Define {0}.permission "
                "or override {0}.get_permission().".format(self.__class__.__name__)
            )
        return self.permission

    def get_permission_object(self):
        return getattr(self, "permission_object", None)

    def grant_permission(self):
        for perm in self.get_permission():
            obj = self.get_permission_object()
            assign_perm(perm, self.user, obj)

    def login_permitted_user(self):
        self.grant_permission()
        self.client.login(username="john", password="pass")

    def test_status_code_for_anonymous_user(self):
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, self.status_anonymous)

    def test_status_code_for_signed_user(self):
        self.client.login(username="john", password="pass")
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, self.status_no_permission)

    def test_status_code_for_privileged_user(self):
        self.grant_permission()
        self.client.login(username="john", password="pass")
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, self.status_has_permission)
