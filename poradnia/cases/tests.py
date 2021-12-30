from datetime import timedelta

import django
from atom.ext.guardian.tests import PermissionStatusMixin
from atom.mixins import AdminTestCaseMixin
from django.contrib.admin.sites import AdminSite
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.test import RequestFactory
from django.test.utils import override_settings
from django.utils import timezone
from guardian.shortcuts import assign_perm, remove_perm
from test_plus.test import TestCase

from poradnia.cases.admin import CaseAdmin
from poradnia.cases.factories import (
    CaseFactory,
    PermissionGroupFactory,
    CaseUserObjectPermissionFactory,
)
from poradnia.cases.filters import StaffCaseFilter
from poradnia.cases.forms import CaseCloseForm
from poradnia.cases.models import Case, PermissionGroup
from poradnia.cases.views import CaseListView
from poradnia.events.factories import EventFactory
from poradnia.letters.factories import LetterFactory
from poradnia.letters.models import Letter
from poradnia.users.factories import UserFactory

from django.urls import reverse


class CaseQuerySetTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_for_assign_cant(self):
        self.assertFalse(
            Case.objects.for_user(self.user).filter(pk=CaseFactory().pk).exists()
        )

    def test_for_user_cant(self):
        self.assertFalse(
            Case.objects.for_user(self.user).filter(pk=CaseFactory().pk).exists()
        )

    def test_for_user_can_local_view(self):
        assign_perm("cases.can_view", self.user)
        self.assertTrue(
            Case.objects.for_user(self.user).filter(pk=CaseFactory().pk).exists()
        )

    def test_for_user_can_global_view(self):
        case = CaseFactory()
        assign_perm("cases.can_view", self.user, case)
        self.assertTrue(Case.objects.for_user(self.user).filter(pk=case.pk).exists())

    def test_for_assign_can_view_client(self):  # perm set by signal
        self.assertTrue(
            Case.objects.for_assign(self.user)
            .filter(pk=CaseFactory(created_by=self.user).pk)
            .exists()
        )

    def test_for_assign_can_view_created(self):  # perm set by signal
        self.assertTrue(
            Case.objects.for_assign(self.user)
            .filter(pk=CaseFactory(client=self.user).pk)
            .exists()
        )

    def test_for_assign_no_duplicates_with_multiple_permissions(self):
        assign_perm("cases.can_view", self.user)
        assign_perm("cases.can_assign", self.user)
        case = CaseFactory(created_by=self.user)
        self.assertEqual(1, len(Case.objects.for_assign(self.user)))

    def test_with_perm(self):
        CaseFactory.create_batch(size=25)
        with self.assertNumQueries(2):
            qs = Case.objects.with_perm().all()
            for obj in qs:
                list(obj.caseuserobjectpermission_set.all())

    def test_with_record_count(self):
        obj = CaseFactory()
        LetterFactory.create_batch(size=25, case=obj)
        self.assertEqual(
            Case.objects.filter(pk=obj.pk).with_record_count().get().record_count, 25
        )

    def test_by_involved_in(self):
        # TODO
        self.assertTrue(True)

    def test_by_msg(self):
        # TODO
        self.assertTrue(True)

    def test_order_for_user(self):
        a = repr(
            CaseFactory(
                name="CaseA",
                last_action=timezone.now() + timedelta(days=0),
                last_send=timezone.now() + timedelta(days=+1),
            )
        )
        b = repr(
            CaseFactory(
                name="CaseB",
                last_action=timezone.now() + timedelta(days=+2),
                last_send=timezone.now() + timedelta(days=-1),
            )
        )
        c = repr(
            CaseFactory(
                name="CaseC",
                last_action=timezone.now() + timedelta(days=-1),
                last_send=timezone.now() + timedelta(days=+3),
            )
        )
        user = UserFactory(is_staff=True)
        self.assertQuerysetEqual(
            Case.objects.order_for_user(user, True).all(), [c, a, b]
        )
        self.assertQuerysetEqual(
            Case.objects.order_for_user(user, False).all(), [b, a, c]
        )
        user = UserFactory(is_staff=False)
        self.assertQuerysetEqual(
            Case.objects.order_for_user(user, True).all(), [b, a, c]
        )
        self.assertQuerysetEqual(
            Case.objects.order_for_user(user, False).all(), [c, a, b]
        )


class CaseTestCase(TestCase):
    def setUp(self):
        self.object = CaseFactory()

    def test_get_edit_url(self):
        self.assertEqual(CaseFactory(pk=50).get_edit_url(), "/sprawy/sprawa-50/edytuj/")

    def test_perm_check(self):
        u1 = UserFactory()
        assign_perm("cases.can_view", u1)

        u2 = UserFactory()
        assign_perm("cases.can_view", u2, self.object)

        self.assertTrue(self.object.perm_check(u1, "can_view"))
        self.assertTrue(self.object.perm_check(u2, "can_view"))
        with self.assertRaises(PermissionDenied):
            self.object.perm_check(UserFactory(), "can_view")

    def test_has_assignees_lifecycle(self):
        user = UserFactory(is_staff=True)
        self.assertFalse(self.object.has_assignees())

        permission = CaseUserObjectPermissionFactory(
            content_object=self.object,
            permission_name="can_send_to_client",
            user=user,
        )
        self.assertTrue(self.object.has_assignees())

        permission.delete()
        self.assertFalse(self.object.has_assignees())

    def test_has_assignees_non_staff(self):
        user = UserFactory(is_staff=False)
        assign_perm("cases.can_send_to_client", user, self.object)
        self.assertFalse(self.object.has_assignees())

    def test_has_assignees_other_case(self):
        user = UserFactory(is_staff=True)
        other_object = CaseFactory()
        assign_perm("cases.can_send_to_client", user, other_object)
        self.assertFalse(self.object.has_assignees())

    def test_status_update_reopen(self):
        self.object.status = Case.STATUS.closed
        self.object.status_update(reopen=False)
        self.assertEqual(self.object.status, Case.STATUS.closed)
        self.object.status_update(reopen=True)
        self.assertEqual(self.object.status, Case.STATUS.free)

    def test_status_update_reopen_with_assignee(self):
        assign_perm("cases.can_send_to_client", UserFactory(is_staff=True), self.object)
        self.object.status = Case.STATUS.closed
        self.object.status_update(reopen=False)
        self.assertEqual(self.object.status, Case.STATUS.closed)
        self.object.status_update(reopen=True)
        self.assertEqual(self.object.status, Case.STATUS.assigned)

    def test_status_for_moderated(self):
        assign_perm("cases.can_view", UserFactory(is_staff=True), self.object)
        self.object.status_update()
        self.assertEqual(self.object.status, Case.STATUS.moderated)

    def test_update_counters_last_received_default(self):
        self.object.update_counters()
        self.assertEqual(self.object.last_received, None)

    def _make_letter(self):  # Hack for Travis
        o = LetterFactory(case=self.object, created_by__is_staff=False)
        return Letter.objects.get(pk=o.pk)

    def test_update_counters_last_received_setup(self):
        l = self._make_letter()
        self.object.update_counters()
        self.assertEqual(l.created_on, self.object.last_received)

    def test_update_counters_last_received_update(self):
        self._make_letter()
        self.object.update_counters()
        new = self._make_letter()
        self.object.update_counters()
        self.assertEqual(new.created_on, self.object.last_received)

    def test_update_counters_hide_past_deadline(self):
        event = EventFactory(
            time=timezone.now() - timedelta(days=5), deadline=True, case=self.object
        )
        self.object.update_counters()
        self.assertEqual(self.object.deadline, None)

    def test_update_counters_show_future_deadline(self):
        event = EventFactory(
            time=timezone.now() + timedelta(days=5), deadline=True, case=self.object
        )
        self.object.update_counters()
        self.assertEqual(self.object.deadline, event)


class CaseUserObjectPermissionTestCase(TestCase):
    def case_with_assignees(
        self, case_status, staff_assignees=0, non_staff_assignees=0
    ):
        """
        Build a case with a given set of assignees and set its status afterwards.

        Will throw if provided params result in a volatile case, i.e. one that might change its status on the first `status_update` call. Such cases are not feasible for testing status restoration.
        """
        perm_id = "cases.can_send_to_client"
        case = CaseFactory()
        for i in range(staff_assignees):
            assign_perm(perm_id, UserFactory(is_staff=True), case)

        for i in range(non_staff_assignees):
            assign_perm(perm_id, UserFactory(is_staff=False), case)

        case.status = case_status
        case.save()

        # Check if the status is valid, i.e. didn't change on the status update after making no changes.
        case.status_update()
        if case.status != case_status:
            raise Exception(
                f"Invalid case specified. Status changed to {case.status} after first update. Expected {case_status}."
            )

        return case

    def test_updates_status(self):
        """
        Test that granting the permission sets the correct case status.
        """
        user_non_staff = UserFactory(is_staff=False)
        user_staff = UserFactory(is_staff=True)

        data = [
            {
                "case": self.case_with_assignees(
                    Case.STATUS.free, staff_assignees=0, non_staff_assignees=0
                ),
                "user": user_staff,
                "expected_status": Case.STATUS.assigned,
            },
            {
                "case": self.case_with_assignees(
                    Case.STATUS.free, staff_assignees=0, non_staff_assignees=0
                ),
                "user": user_non_staff,
                "expected_status": Case.STATUS.free,
            },
            {
                "case": self.case_with_assignees(
                    Case.STATUS.free, staff_assignees=0, non_staff_assignees=1
                ),
                "user": user_staff,
                "expected_status": Case.STATUS.assigned,
            },
            {
                "case": self.case_with_assignees(
                    Case.STATUS.assigned, staff_assignees=1, non_staff_assignees=0
                ),
                "user": user_staff,
                "expected_status": Case.STATUS.assigned,
            },
            {
                "case": self.case_with_assignees(
                    Case.STATUS.closed, staff_assignees=0, non_staff_assignees=0
                ),
                "user": user_staff,
                "expected_status": Case.STATUS.closed,
            },
            {
                "case": self.case_with_assignees(
                    Case.STATUS.closed, staff_assignees=0, non_staff_assignees=0
                ),
                "user": user_non_staff,
                "expected_status": Case.STATUS.closed,
            },
        ]

        for i, datum in enumerate(data):
            with self.subTest(i=i):
                case = datum["case"]
                user = datum["user"]
                expected_status = datum["expected_status"]

                status_before = case.status

                assign_perm("cases.can_send_to_client", user, case)
                self.assertEqual(
                    case.status, expected_status, "Status not set to expected value."
                )

                remove_perm("cases.can_send_to_client", user, case)

                # Manually update status, as `remove_perm` doesn't trigger the `delete` logic.
                case.status_update(save=True)
                case.refresh_from_db()

                self.assertEqual(case.status, status_before, "Status not restored.")


class CaseDetailViewTestCase(TestCase):
    def setUp(self):
        self.object = CaseFactory()
        self.client.login(username=self.object.created_by.username, password="pass")

    def test_can_view(self):
        self.client.get(self.object.get_absolute_url())

    def test_display_letter(self):
        obj = LetterFactory(case=self.object)
        resp = self.client.get(self.object.get_absolute_url())
        self.assertContains(resp, obj.name)

    def test_hide_internal_letter(self):
        obj = LetterFactory(case=self.object, status="staff")
        obj2 = LetterFactory(case=self.object, status="done")
        self.object.created_by.is_staff = False
        self.object.created_by.save()
        resp = self.client.get(self.object.get_absolute_url())
        self.assertNotContains(resp, obj.name)
        self.assertContains(resp, obj2.name)


class StaffCaseFilterTestCase(TestCase):
    def get_filter(self, *args, **kwargs):
        return StaffCaseFilter(queryset=Case.objects.all(), *args, **kwargs)

    def get_permission_filter_qs(self, user, **kwargs):
        admin = UserFactory(is_staff=True, is_superuser=True)
        return self.get_filter(user=admin, data={"permission": user.pk}).qs.filter(
            **kwargs
        )

    def test_permission_filter(self):
        obj = CaseFactory()
        self.assertFalse(
            self.get_permission_filter_qs(
                user=UserFactory(is_staff=True), pk=obj.pk
            ).exists()
        )
        user = UserFactory(is_staff=True)
        assign_perm("cases.can_view", user, obj)
        self.assertTrue(self.get_permission_filter_qs(user=user, pk=obj.pk).exists())

    def test_form_fields(self):
        su_user = UserFactory(is_staff=True, is_superuser=True)
        self.assertCountEqual(
            self.get_filter(user=su_user).form.fields.keys(),
            [
                "status",
                "handled",
                "id",
                "client",
                "name",
                "has_project",
                "permission",
                "has_advice",
                "o",
            ],
        )
        self.assertCountEqual(
            self.get_filter(user=UserFactory(is_staff=True)).form.fields.keys(),
            [
                "status",
                "handled",
                "id",
                "client",
                "name",
                "has_project",
                "permission",
                "has_advice",
                "o",
            ],
        )


class CaseListViewTestCase(TestCase):
    url = reverse_lazy("cases:list")

    def setUp(self):
        self.user = UserFactory(username="john")
        self.case = CaseFactory()

    def _test_filtersetclass(self, expect, user):
        self.factory = RequestFactory()
        req = self.factory.get("/")
        req.user = user
        view = CaseListView.as_view()
        resp = view(req)
        view_for_req = resp.context_data["view"]
        self.assertEqual(view_for_req.get_filterset_class() == StaffCaseFilter, expect)

    def test_filtersetclass_for_staff(self):
        self._test_filtersetclass(True, UserFactory(is_staff=True))
        self._test_filtersetclass(False, UserFactory(is_staff=False))

    def test_hide_cases_without_permission(self):
        self.assertTrue(self.client.login(username="john", password="pass"))

        resp = self.client.get(self.url)

        self.assertNotContains(resp, self.case)

    def test_show_cases_with_global_permission(self):
        assign_perm("cases.can_view", self.user)

        self.assertTrue(self.client.login(username="john", password="pass"))

        resp = self.client.get(self.url)

        self.assertContains(resp, self.case)

    def test_respect_local_can_view_permission(self):
        assign_perm("can_view", self.user, self.case)

        self.assertTrue(self.client.login(username="john", password="pass"))

        resp = self.client.get(self.url)

        self.assertContains(resp, self.case)


class CaseAdminTestCase(AdminTestCaseMixin, TestCase):
    user_factory_cls = UserFactory
    factory_cls = CaseFactory
    model = Case

    def setUp(self):
        self.site = AdminSite()
        super().setUp()

    def assertIsValid(
        self, model_admin, model
    ):  # See django/tests/modeladmin/tests.py#L602
        admin_obj = model_admin(model, self.site)
        if django.VERSION > (1, 9):
            errors = admin_obj.check()
        else:
            errors = admin_obj.check(model)
        expected = []
        self.assertEqual(errors, expected)

    def test_is_valid(self):
        self.assertIsValid(CaseAdmin, Case)

    def test_record_count(self):
        case = CaseFactory()
        LetterFactory.create_batch(size=25, case=case)
        admin_obj = CaseAdmin(Case, AdminSite())
        request = RequestFactory().get(reverse_lazy("admin:cases_case_changelist"))
        request.user = UserFactory(is_staff=True, is_superuser=True)
        qs = admin_obj.get_queryset(request)
        obj = qs.get(pk=case.pk)
        self.assertTrue(hasattr(obj, "record_count"))
        self.assertEqual(admin_obj.record_count(obj), 25)


class CaseCloseViewTestCase(PermissionStatusMixin, TestCase):
    permission = ["cases.can_close_case"]

    def setUp(self):
        self.user = UserFactory(username="john", password="pass")
        self.object = self.permission_object = CaseFactory()
        self.url = self.object.get_close_url()

    def test_close_case(self):
        self.login_permitted_user()
        resp = self.client.post(self.url, {"notify": True}, follow=True)
        self.object.refresh_from_db()
        self.assertEqual(self.object.status, Case.STATUS.closed)


class CaseCloseFormTestCase(TestCase):
    form = CaseCloseForm

    def setUp(self):
        self.user = UserFactory()
        self.object = CaseFactory()

    def test_close_notify(self):
        self.form({"notify": False}, user=self.user, instance=self.object).save()
        self.assertEqual(len(mail.outbox), 0)
        self.form({"notify": True}, user=self.user, instance=self.object).save()
        self.assertEqual(len(mail.outbox), 1)


class UserPermissionCreateViewTestCase(PermissionStatusMixin, TestCase):
    permission = ["cases.can_manage_permission", "cases.can_assign"]

    def setUp(self):
        self.user = UserFactory(username="john", password="pass")
        self.user_with_permission = UserFactory()
        self.permission_object = None  # use global perms
        self.object = CaseFactory()
        self.url = reverse("cases:permission_add", kwargs={"pk": self.object.pk})

    def test_view_loads_correctly(self):
        self.login_permitted_user()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.object.name)

    def test_invalid_user_used(self):
        self.login_permitted_user()
        resp = self.client.post(
            self.url,
            data={"users": [self.user_with_permission.pk], "permissions": ["can_view"]},
        )
        self.assertEqual(resp.status_code, 200)

    def test_valid_user_used(self):
        self.login_permitted_user()
        assign_perm("users.can_view_other", self.user)
        resp = self.client.post(
            self.url,
            data={"users": [self.user_with_permission.pk], "permissions": ["can_view"]},
        )
        self.assertEqual(resp.status_code, 302)


class CaseGroupPermissionViewTestCase(PermissionStatusMixin, TestCase):
    permission = ["cases.can_manage_permission", "cases.can_assign"]

    def setUp(self):
        self.user = UserFactory(username="john")
        self.user_with_permission = UserFactory(is_staff=True)
        self.object = CaseFactory()
        self.url = reverse("cases:permission_grant", kwargs={"pk": self.object.pk})

    def test_view_loads_correctly(self):
        self.login_permitted_user()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.object.name)

    def test_assign_permission(self):
        self.login_permitted_user()
        self.assertFalse(
            self.user_with_permission.has_perm("can_send_to_client", self.object)
        )

        pg = PermissionGroupFactory(permissions=("can_send_to_client",))
        resp = self.client.post(
            self.url, data={"user": self.user_with_permission.pk, "group": pg.pk}
        )
        self.assertEqual(resp.status_code, 302)

        self.assertTrue(
            self.user_with_permission.has_perm("cases.can_send_to_client", self.object)
        )

    def test_remove_existing_perm(self):
        self.login_permitted_user()
        assign_perm("cases.can_view", self.user_with_permission, self.object)
        pg = PermissionGroupFactory(permissions=("can_send_to_client",))
        resp = self.client.post(
            self.url, data={"user": self.user_with_permission.pk, "group": pg.pk}
        )
        self.assertEqual(resp.status_code, 302)

        self.assertTrue(
            self.user_with_permission.has_perm("cases.can_send_to_client", self.object)
        )
        self.assertFalse(
            self.user_with_permission.has_perm("cases.can_view", self.object)
        )


class PermissionGroupAdminTestCase(AdminTestCaseMixin, TestCase):
    user_factory_cls = UserFactory
    factory_cls = PermissionGroupFactory
    model = PermissionGroup


class UserPermissionRemoveViewTestCase(PermissionStatusMixin, TestCase):
    permission = ["cases.can_manage_permission", "cases.can_assign"]

    def setUp(self):
        self.subject_user = UserFactory()
        self.user = UserFactory(username="john")
        self.object = CaseFactory()

    def get_url(self):
        return reverse(
            "cases:permission_remove",
            kwargs={"pk": self.object.pk, "username": self.subject_user.username},
        )
