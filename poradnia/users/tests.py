import json

from atom.mixins import AdminTestCaseMixin
from django.core import mail
from django.test import RequestFactory
from django.utils import timezone
from guardian.shortcuts import assign_perm, get_perms
from test_plus.test import TestCase
from .factories import UserFactory
from django.urls import reverse

from poradnia.cases.factories import CaseFactory
from poradnia.cases.models import Case
from poradnia.users.factories import StaffFactory, UserFactory
from poradnia.users.forms import (
    TranslatedManageObjectPermissionForm,
    TranslatedUserObjectPermissionsForm,
    UserForm,
)
from poradnia.users.models import User
from poradnia.users.views import UserAutocomplete

from django.urls import reverse, reverse_lazy


class UserTestCase(TestCase):
    def test_get_user_by_get_by_email_or_create(self):
        self.assertEqual(User.objects.count(), 1)
        new_user = User.objects.get_by_email_or_create("sarah@example.com")
        self.assertEqual(User.objects.count(), 2)
        get_user = User.objects.get_by_email_or_create("sarah@example.com")
        self.assertEqual(new_user, get_user)
        self.assertEqual(User.objects.count(), 2)

    def _create_user(self, email, username):
        User.objects.email_to_unique_username(email)
        self.assertEqual(username, username)
        User.objects.create_user(username=username)

    def test_email_to_username(self):
        self._create_user("example@example.com", "example_example_com")
        for i in range(1, 11):
            self._create_user("example@example.com", "example_example_com-" + str(i))
        with self.assertRaises(ValueError):
            self._create_user("example@example.com", "example_example_com-11")

    def test_login_email(self):  # Test for regresion #204
        max_length = User._meta.get_field("username").max_length
        email = "very-long-email-which-make-broken-username@example.com"
        self.assertLessEqual(
            len(User.objects.email_to_unique_username(email)), max_length
        )

    def test_has_picture(self):
        self.assertTrue(UserFactory().picture)

    def test_has_codename(self):
        self.assertTrue(UserFactory().codename)

    def test_get_codename(self):
        self.assertEqual(User(username="X", codename="ELA").get_codename(), "ELA")
        self.assertEqual(User(username="X").get_codename(), "X")

    def test_get_nicename(self):
        self.assertEqual(
            User(username="X", first_name="John", last_name="Smith").get_codename(),
            "John Smith",
        )
        self.assertEqual(User(username="X").get_codename(), "X")

    def test_created_on(self):
        now = timezone.now()
        created_on = UserFactory().created_on
        diff_seconds = (created_on - now).total_seconds()
        self.assertLess(diff_seconds, 5)  # allow small latency


class UserQuerySetTestCase(TestCase):
    def test_for_user_manager(self):
        UserFactory()
        u1 = UserFactory()
        u2 = UserFactory(is_staff=True)
        u3 = UserFactory(is_staff=True, is_superuser=True)
        self.assertEqual(
            User.objects.for_user(u1).registered().count(), 3
        )  # self + 2 staff
        self.assertEqual(
            User.objects.for_user(u2).registered().count(), 2
        )  # 2 staff with self
        self.assertEqual(User.objects.for_user(u3).registered().count(), 4)  # all

    def test_with_case_count(self):
        user = UserFactory()
        CaseFactory.create_batch(size=25, client=user)
        self.assertEqual(User.objects.with_case_count().get(pk=user.pk).case_count, 25)
        self.assertEqual(
            User.objects.with_case_count().get(pk=UserFactory().pk).case_count, 0
        )

    def test_with_case_count_assigned(self):
        user = UserFactory()
        self.assertEqual(
            User.objects.with_case_count_assigned().get(pk=user.pk).case_assigned_sum, 0
        )

        SIZE_PATTERN = [
            (1, Case.STATUS.free),
            (2, Case.STATUS.assigned),
            (3, Case.STATUS.closed),
        ]
        for size, status in SIZE_PATTERN:
            for obj in CaseFactory.create_batch(size=size, status=status):
                assign_perm("cases.can_view", user, obj)
        user = User.objects.with_case_count_assigned().get(pk=user.pk)
        self.assertEqual(user.case_assigned_free, 1)
        self.assertEqual(user.case_assigned_active, 2)
        self.assertEqual(user.case_assigned_closed, 3)
        self.assertEqual(user.case_assigned_sum, 6)

        SIZE_PATTERN_UPDATED = [
            (4, Case.STATUS.free),
            (5, Case.STATUS.assigned),
            (6, Case.STATUS.closed),
        ]
        for size, status in SIZE_PATTERN_UPDATED:
            for obj in CaseFactory.create_batch(size=size, status=status):
                assign_perm("cases.can_view", user, obj)
        user_updated = User.objects.with_case_count_assigned().get(pk=user.pk)
        self.assertEqual(user_updated.case_assigned_free, 5)
        self.assertEqual(user_updated.case_assigned_active, 7)
        self.assertEqual(user_updated.case_assigned_closed, 9)
        self.assertEqual(user_updated.case_assigned_sum, 21)

    def _register_email_count(self, notify, count):
        u = User.objects.register_email(email="sarah@example.com", notify=notify)
        self.assertEqual(len(mail.outbox), count)
        self.assertEqual(User.objects.get(email="sarah@example.com"), u)

    def test_register_email_no_notify(self):
        self._register_email_count(notify=True, count=1)

    def test_register_email_notify(self):
        self._register_email_count(notify=False, count=0)


class UserFormTestCase(TestCase):
    def test_has_avatar(self):
        self.assertIn("picture", UserForm().fields)

    def test_codename_visibility(self):
        # Show for staff
        self.assertIn("codename", UserForm(instance=UserFactory(is_staff=True)).fields)
        # Non-show for non-staff
        self.assertNotIn(
            "codename", UserForm(instance=UserFactory(is_staff=False)).fields
        )
        # Non show for new object
        self.assertNotIn("codename", UserForm().fields)


class UserDetailViewTestCase(TestCase):
    def setUp(self):
        self.object = UserFactory(is_staff=False)
        self.url = self.object.get_absolute_url()
        self.client_filter_url = (
            reverse("cases:list") + "?client=" + str(self.object.pk)
        )
        self.permission_filter_url = (
            reverse("cases:list") + "?permission=" + str(self.object.pk)
        )

    def test_no_redirect_loop_if_no_auth(self):
        resp = self.client.get(self.url, follow=True)
        self.assertLess(len(resp.redirect_chain), 1)
        self.assertEqual(resp.status_code, 403)

    def test_can_view_self(self):
        self.client.login(username=self.object.username, password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_need_permission(self):
        user = UserFactory()
        self.client.login(username=user.username, password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_has_permission_to_view(self):
        user = UserFactory()
        assign_perm("users.can_view_other", user)
        self.client.login(username=user.username, password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_has_link_to_self_assigned_cases(self):
        self.client.login(username=self.object.username, password="pass")
        resp = self.client.get(self.url)
        self.assertContains(resp, self.client_filter_url)
        self.assertNotContains(resp, self.permission_filter_url)

    def test_has_link_to_user_assigned_cases(self):
        user = UserFactory()
        assign_perm("users.can_view_other", user)
        assign_perm("cases.can_assign", user)
        self.client.login(username=user.username, password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.client_filter_url)
        self.assertContains(resp, self.permission_filter_url)


class UserListViewTestCase(TestCase):
    url = reverse_lazy("users:list")

    def setUp(self):
        self.user_list = UserFactory.create_batch(size=1, is_staff=False)
        self.staff_list = UserFactory.create_batch(size=1, is_staff=True)
        self.object_list = self.user_list + self.staff_list

    def test_permission_access_and_filter(self):
        self.client.login(username=UserFactory().username, password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

        self.client.login(username=UserFactory(is_staff=True).username, password="pass")
        resp = self.client.get(self.url)
        self.assertContains(resp, self.staff_list[0].username)
        self.assertNotContains(resp, self.user_list[0].username)

        user = UserFactory(is_staff=True)
        assign_perm("users.can_view_other", user)
        self.client.login(username=user.username, password="pass")
        resp = self.client.get(self.url)
        self.assertContains(resp, self.object_list[0].username)
        self.assertContains(resp, self.object_list[0].username)

    def test_contains_filter(self):
        self.client.login(username=UserFactory(is_staff=True).username, password="pass")
        resp = self.client.get(self.url)
        self.assertIn("filter", resp.context)

    def get_view(self, **kwargs):
        return self.client.get(self.url, data=kwargs).context_data["view"]

    def test_get_is_staff_choice(self):
        self.client.login(username=UserFactory(is_staff=True).username, password="pass")
        self.assertEqual(self.get_view().get_is_staff_choice(), 0)  # Default
        self.assertEqual(
            self.get_view(is_staff="a").get_is_staff_choice(), 0
        )  # Non-num
        self.assertEqual(
            self.get_view(is_staff="5").get_is_staff_choice(), 0
        )  # Too large
        self.assertEqual(self.get_view(is_staff=1).get_is_staff_choice(), 1)  # Correct

    def _test_get_queryset(self, iss, **kwargs):
        qs = self.get_view(**kwargs).get_queryset()
        qs = qs.filter(pk=UserFactory(is_staff=iss).pk)
        return qs.exists()

    def test_get_queryset_is_staff_choice(self):
        self.client.login(
            username=UserFactory(is_staff=True, is_superuser=True).username,
            password="pass",
        )
        # 0 - _
        self.assertTrue(self._test_get_queryset(iss=True))
        self.assertTrue(self._test_get_queryset(iss=False))
        # 1 - is_staff=True
        self.assertTrue(self._test_get_queryset(iss=True, is_staff="1"))
        self.assertFalse(self._test_get_queryset(iss=False, is_staff="1"))
        # 2 - is_staff=False
        self.assertTrue(self._test_get_queryset(iss=False, is_staff="2"))
        self.assertFalse(self._test_get_queryset(iss=True, is_staff="2"))

    def test_get_context_data_is_staff(self):
        self.client.login(
            username=UserFactory(is_staff=True, is_superuser=True).username,
            password="pass",
        )
        resp = self.client.get(self.url, data={"is_staff": 1})
        context_data = resp.context_data
        self.assertIn("is_staff", context_data)
        self.assertEqual(context_data["is_staff"]["selected"], 1)
        self.assertIn("choices", context_data["is_staff"])


class LoginPageTestCase(TestCase):
    url = reverse_lazy("account_login")

    def test_login_page_integrate(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, "<form ")
        self.assertContains(resp, "login")
        self.assertContains(resp, "password")


class TranslatedUserObjectPermissionsFormTestCase(TestCase):
    def setUp(self):
        self.obj = UserFactory()
        self.user = UserFactory()

    def test_delete_all_permissions(self):
        assign_perm("users.change_user", self.user, self.obj)
        self.assertTrue(self.user.has_perm("users.change_user", self.obj))
        form = TranslatedUserObjectPermissionsForm(
            data={"permissions": ""}, user=self.user, obj=self.obj
        )
        self.assertTrue(form.is_valid())
        form.save_obj_perms()
        self.assertFalse(self.user.has_perm("users.change_user", self.obj))
        self.assertEqual(get_perms(self.user, self.obj), [])


class TranslatedManageObjectPermissionFormTestCase(TestCase):
    def test_limit_choices_of_users(self):
        obj = UserFactory()
        managed_user = UserFactory()
        form = TranslatedManageObjectPermissionForm(
            data={"permissions": ["change_user"], "users": [managed_user.pk]},
            actor=managed_user,
            obj=obj,
        )
        self.assertTrue(form.is_valid())
        form = TranslatedManageObjectPermissionForm(
            data={"permissions": ["change_user"], "users": [UserFactory().pk]},
            actor=managed_user,
            obj=obj,
        )
        self.assertFalse(form.is_valid())


class UserProfileViewTestCase(TestCase):
    url = reverse("users:profile")
    login_page = reverse("account_login")

    def setUp(self):
        self.regular_user = UserFactory()
        self.staff_user = StaffFactory()

    def test_profile_page_not_visible_for_anonymous(self):
        response = self.client.get(self.url)
        self.assertIn(self.login_page, response.url)

    def test_profile_page_visible_for_authenticated(self):
        self.client.login(username=self.regular_user.username, password="pass")

        response = self.client.get(self.url)
        self.assertContains(response, self.regular_user.username)

    def test_event_reminder_setting_visible_for_staff_only(self):
        self.client.login(username=self.regular_user.username, password="pass")

        response = self.client.get(self.url)
        self.assertNotContains(response, "reminder")

        self.client.login(username=self.staff_user.username, password="pass")

        response = self.client.get(self.url)
        self.assertContains(response, "reminder")

    def test_store_user_profile(self):
        self.client.login(username=self.regular_user.username, password="pass")
        www = "http://example.com"
        description = "asd"

        response = self.client.post(self.url, {"www": www, "description": description})

        expected_redirect = reverse(
            "users:detail", kwargs={"username": self.regular_user.username}
        )
        self.assertRedirects(response, expected_redirect)

        self.assertEqual(self.regular_user.profile.www, www)
        self.assertEqual(self.regular_user.profile.description, description)


class UserAutocompleteViewTestCase(TestCase):
    def setUp(self):
        self.regular_user = UserFactory()
        self.staff_user = StaffFactory()
        self.factory = RequestFactory()

    def test_staff_user_with_permission_can_view_regular_user(self):
        request = self.factory.get("?q={}".format(self.regular_user.username))
        request.user = self.staff_user
        assign_perm("users.can_view_other", self.staff_user)
        response = UserAutocomplete.as_view()(request=request).getvalue()
        response = response.decode("utf-8")
        response_json = json.loads(response)
        self.assertEqual(len(response_json["results"]), 1)
        self.assertEqual(response_json["results"][0]["text"], str(self.regular_user))

    def test_staff_user_with_permission_can_not_view_reqular_user(self):
        request = self.factory.get("?q={}".format(self.regular_user.username))
        request.user = self.staff_user
        response = UserAutocomplete.as_view()(request=request)
        self.assertNotContains(response, self.regular_user)


class UserAdminTestCase(AdminTestCaseMixin, TestCase):
    user_factory_cls = UserFactory
    factory_cls = UserFactory
    model = User


class ObjectMixin:
    def setUp(self):
        self.user = self.object =  UserFactory(username="john")


class UserDeassignViewTestCase(ObjectMixin, TestCase):

    def get_url(self):
        return reverse("users:deassign", kwargs={"username": self.object.username})

    def login_permitted(self):
        self.client.login(username="john", password="pass")
        assign_perm('cases.can_assign', self.user)

    def test_show_form_no_error(self):
        # Given
        self.login_permitted()
        # When & Then
        self.get_check_200(self.get_url())

    def test_perform_successfully_for_staff(self):
        # Given
        self.login_permitted()
        case = CaseFactory()
        assign_perm('cases.can_view', self.user, case)
        # When
        self.client.post(self.get_url())
        # Then
        self.assertNotIn('can_view', self.user.get_all_permissions(case))

    def test_keep_permission_for_client(self):
        self.login_permitted()
        # Given
        case = CaseFactory()
        assign_perm('cases.can_view', case.client, case)
        # When
        self.client.post(self.get_url())
        # Then
        self.assertIn('can_view', case.client.get_all_permissions(case))