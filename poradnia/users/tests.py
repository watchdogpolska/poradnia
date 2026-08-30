import re
from datetime import datetime, timedelta
from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.test import RequestFactory, override_settings
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.html import escape
from django.utils.http import urlsafe_base64_encode
from guardian.shortcuts import assign_perm, get_perms
from test_plus.test import TestCase

from poradnia.cases.factories import CaseFactory
from poradnia.cases.models import Case
from poradnia.users.factories import StaffFactory, UserFactory
from poradnia.users.forms import (
    TranslatedManageObjectPermissionForm,
    TranslatedUserObjectPermissionsForm,
    UserForm,
)
from poradnia.users.models import User
from poradnia.users.tokens import (
    AccountActivationTokenGenerator,
    account_activation_token,
)
from poradnia.users.views import UserAutocomplete
from poradnia.utils.tests.mixins import AdminTestCaseMixin

from .factories import UserFactory


class UserTestCase(TestCase):
    def test_get_user_by_get_by_email_or_create(self):
        self.assertEqual(User.objects.count(), 1)
        new_user = User.objects.get_by_email_or_create("sarah@example.com")
        self.assertEqual(User.objects.count(), 2)
        get_user = User.objects.get_by_email_or_create("sarah@example.com")
        self.assertEqual(new_user, get_user)
        self.assertEqual(User.objects.count(), 2)

    def _create_user(self, email, username):
        unique_username = User.objects.email_to_unique_username(email)
        self.assertEqual(username, unique_username)
        User.objects.create_user(email=email, username=username)

    def test_email_to_username(self):
        print("Testing example0@example.com user creation")
        self._create_user("example0@example.com", "example__example_com")
        for i in range(1, 9):
            print(f"Testing example{i}@example.com user creation")
            self._create_user(f"example{i}@example.com", f"example__example_com-{i}")
        with self.assertRaises(ValueError):
            print("Testing example9@example.com user creation")
            self._create_user("example9@example.com", "example__example_com-9")

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

    def test_for_user_manager_with_client_for_staff(self):
        """
        Client (User) should be visible to the staff who handles his case
        """
        client = UserFactory()
        actor = UserFactory(is_staff=True)
        case = CaseFactory(client=client)

        self.assertEqual(User.objects.for_user(actor).filter(pk=client.pk).count(), 0)
        assign_perm("cases.can_view", actor, case)
        self.assertEqual(User.objects.for_user(actor).filter(pk=client.pk).count(), 1)

    def test_for_user_manager_with_client_for_user(self):
        """
        A user must be a staff to see other users, even if they have access other client cases
        """
        client = UserFactory()
        actor = UserFactory()
        case = CaseFactory(client=client)

        self.assertEqual(User.objects.for_user(actor).filter(pk=client.pk).count(), 0)
        assign_perm("cases.can_view", actor, case)
        self.assertEqual(User.objects.for_user(actor).filter(pk=client.pk).count(), 0)

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

    def _register_by_email_count(self, notify, count):
        u = User.objects.register_by_email(email="sarah@example.com", notify=notify)
        self.assertEqual(len(mail.outbox), count)
        self.assertEqual(User.objects.get(email="sarah@example.com"), u)

    def test_register_by_email_no_notify(self):
        self._register_by_email_count(notify=True, count=1)

    def test_register_by_email_notify(self):
        self._register_by_email_count(notify=False, count=0)


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

    def test_generic_user_info_without_permission(self):
        user = UserFactory()
        self.client.login(username=user.username, password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("info", resp.url)

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
        results = re.findall(r'<div data-value="[^"]*">(.*?)</div>', response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], escape(str(self.regular_user)))

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
        self.user = self.object = UserFactory(username="john")


class UserDeassignViewTestCase(ObjectMixin, TestCase):
    def get_url(self):
        return reverse("users:deassign", kwargs={"username": self.object.username})

    def login_permitted(self):
        self.client.login(username="john", password="pass")
        assign_perm("cases.can_assign", self.user)

    def test_show_form_no_error(self):
        # Given
        self.login_permitted()
        # When & Then
        self.get_check_200(self.get_url())

    def test_perform_successfully_for_staff(self):
        # Given
        self.login_permitted()
        case = CaseFactory()
        assign_perm("cases.can_view", self.user, case)
        # When
        self.client.post(self.get_url())
        # Then
        self.assertNotIn("can_view", self.user.get_all_permissions(case))

    def test_keep_permission_for_client(self):
        self.login_permitted()
        # Given
        case = CaseFactory()
        assign_perm("cases.can_view", case.client, case)
        # When
        self.client.post(self.get_url())
        # Then
        self.assertIn("can_view", case.client.get_all_permissions(case))


class AccountActivationViewTestCase(TestCase):
    def setUp(self):
        cache.clear()  # rate-limit counters live in the cache, not the DB
        self.user = User.objects.register_by_email(
            email="unverified@example.com", notify=False
        )

    def get_url(self, user=None, token=None):
        user = user or self.user
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = (
            token if token is not None else account_activation_token.make_token(user)
        )
        return reverse("users:activate", kwargs={"uidb64": uidb64, "token": token})

    def test_unverified_account_has_no_usable_password(self):
        self.assertFalse(self.user.has_usable_password())

    def test_valid_token_shows_form(self):
        resp = self.client.get(self.get_url())
        self.assertContains(resp, "<form")

    def test_invalid_token_rejected(self):
        resp = self.client.get(self.get_url(token="bogus-token"))
        self.assertNotContains(resp, "<form")

    def test_activation_sets_password_and_logs_in(self):
        resp = self.client.post(
            self.get_url(),
            data={
                "new_password1": "a-Very-Str0ng-Pass",
                "new_password2": "a-Very-Str0ng-Pass",
            },
        )
        self.assertRedirects(resp, reverse("cases:list"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.has_usable_password())
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_token_is_single_use(self):
        url = self.get_url()
        self.client.post(
            url,
            data={
                "new_password1": "a-Very-Str0ng-Pass",
                "new_password2": "a-Very-Str0ng-Pass",
            },
        )
        self.client.logout()
        resp = self.client.get(url)
        self.assertNotContains(resp, "<form")

    @override_settings(ACCOUNT_RATE_LIMITS={"account_activation": "2/m/ip"})
    def test_post_beyond_rate_limit_returns_429(self):
        url = self.get_url(token="bogus-token")
        data = {"new_password1": "x", "new_password2": "x"}
        self.client.post(url, data=data)
        self.client.post(url, data=data)
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 429)

    @override_settings(ACCOUNT_RATE_LIMITS={"account_activation": "1/m/ip"})
    def test_get_requests_are_not_rate_limited(self):
        for _ in range(5):
            resp = self.client.get(self.get_url())
        self.assertContains(resp, "<form")


class AccountActivationTokenGeneratorTestCase(TestCase):
    """Activation tokens use their own timeout (30 days), decoupled from
    Django's global PASSWORD_RESET_TIMEOUT (3-day default) - see
    poradnia/users/tokens.py for why."""

    def setUp(self):
        self.user = User.objects.register_by_email(
            email="unverified-token@example.com", notify=False
        )

    def test_token_survives_past_djangos_default_password_reset_timeout(self):
        token = account_activation_token.make_token(self.user)
        with patch.object(
            AccountActivationTokenGenerator,
            "_now",
            return_value=datetime.now() + timedelta(days=4),
        ):
            self.assertTrue(account_activation_token.check_token(self.user, token))

    def test_token_expires_after_its_own_timeout(self):
        token = account_activation_token.make_token(self.user)
        with patch.object(
            AccountActivationTokenGenerator,
            "_now",
            return_value=datetime.now() + timedelta(days=31),
        ):
            self.assertFalse(account_activation_token.check_token(self.user, token))


class AccountActivationResendViewTestCase(TestCase):
    turnstile_data = {"turnstile": "valid-turnstile-response"}

    def setUp(self):
        cache.clear()  # rate-limit counters live in the cache, not the DB
        self.user = User.objects.register_by_email(
            email="unverified-resend@example.com", notify=False
        )

    def get_url(self, user=None):
        user = user or self.user
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        return reverse("users:activate-resend", kwargs={"uidb64": uidb64})

    @patch("turnstile.fields.TurnstileField.validate", return_value=True)
    def test_resend_sends_new_activation_email(self, _mock):
        resp = self.client.post(self.get_url(), data=self.turnstile_data)
        self.assertRedirects(resp, reverse("account_login"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.user.email, mail.outbox[0].to)

    @patch("turnstile.fields.TurnstileField.validate", return_value=True)
    def test_resend_is_noop_for_already_activated_account(self, _mock):
        self.user.set_password("a-Very-Str0ng-Pass")
        self.user.save()
        resp = self.client.post(self.get_url(), data=self.turnstile_data)
        self.assertRedirects(resp, reverse("account_login"))
        self.assertEqual(len(mail.outbox), 0)

    @patch("turnstile.fields.TurnstileField.validate", return_value=True)
    def test_resend_is_noop_for_unknown_uid(self, _mock):
        bogus_uidb64 = urlsafe_base64_encode(force_bytes(999999))
        resp = self.client.post(
            reverse("users:activate-resend", kwargs={"uidb64": bogus_uidb64}),
            data=self.turnstile_data,
        )
        self.assertRedirects(resp, reverse("account_login"))
        self.assertEqual(len(mail.outbox), 0)

    @patch("turnstile.fields.TurnstileField.validate", return_value=True)
    def test_response_is_identical_whether_or_not_the_uid_is_real(self, _mock):
        # Same status code and redirect target either way, so the endpoint
        # can't be used to enumerate which accounts exist.
        bogus_uidb64 = urlsafe_base64_encode(force_bytes(999999))
        real_resp = self.client.post(self.get_url(), data=self.turnstile_data)
        bogus_resp = self.client.post(
            reverse("users:activate-resend", kwargs={"uidb64": bogus_uidb64}),
            data=self.turnstile_data,
        )
        self.assertEqual(real_resp.status_code, bogus_resp.status_code)
        self.assertEqual(real_resp.url, bogus_resp.url)

    @override_settings(ACCOUNT_RATE_LIMITS={"account_activation_resend": "2/m/ip"})
    @patch("turnstile.fields.TurnstileField.validate", return_value=True)
    def test_post_beyond_ip_rate_limit_returns_429(self, _mock):
        url = self.get_url()
        self.client.post(url, data=self.turnstile_data)
        self.client.post(url, data=self.turnstile_data)
        resp = self.client.post(url, data=self.turnstile_data)
        self.assertEqual(resp.status_code, 429)

    @override_settings(
        ACCOUNT_RATE_LIMITS={
            "account_activation_resend": "20/m/ip",
            "account_activation_resend_target": "1/h/key",
        }
    )
    @patch("turnstile.fields.TurnstileField.validate", return_value=True)
    def test_per_account_cap_stops_sending_without_changing_the_response(self, _mock):
        url = self.get_url()
        first = self.client.post(url, data=self.turnstile_data)
        second = self.client.post(url, data=self.turnstile_data)
        self.assertEqual(first.status_code, second.status_code)
        self.assertEqual(first.url, second.url)
        self.assertEqual(len(mail.outbox), 1)
