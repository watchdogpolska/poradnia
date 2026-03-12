from django import forms
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from sorl.thumbnail.admin import AdminImageMixin

from . import admin_mfa  # noqa: F401
from . import admin_socialaccount  # noqa: F401
from .models import Profile, User


class IsSpamUserFilter(admin.SimpleListFilter):
    title = _("Is SPAM user (no login, no cases, no letters)")
    parameter_name = "is_spam_user"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(
                last_login__isnull=True,
                case_client__isnull=True,
                case_created__isnull=True,
                case_modified__isnull=True,
                letter_created_by__isnull=True,
            )
        elif self.value() == "no":
            return queryset.exclude(
                last_login__isnull=True,
                case_client__isnull=True,
                case_created__isnull=True,
                case_modified__isnull=True,
                letter_created_by__isnull=True,
            )
        else:
            return queryset


class NoLoginUserFilter(admin.SimpleListFilter):
    title = _("Has Logged In")
    parameter_name = "has_logged_in_user"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request, queryset):
        if self.value() == "no":
            return queryset.filter(
                last_login__isnull=True,
            )
        elif self.value() == "yes":
            return queryset.exclude(
                last_login__isnull=True,
            )
        else:
            return queryset


class HasCasesUserFilter(admin.SimpleListFilter):
    title = _("Has cases")
    parameter_name = "has_cases_user"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request, queryset):
        if self.value() == "no":
            return queryset.filter(
                case_client__isnull=True,
                case_created__isnull=True,
                case_modified__isnull=True,
            )
        elif self.value() == "yes":
            return queryset.exclude(
                case_client__isnull=True,
                case_created__isnull=True,
                case_modified__isnull=True,
            )
        else:
            return queryset


class HasLettersUserFilter(admin.SimpleListFilter):
    title = _("Has letters")
    parameter_name = "has_letters_user"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request, queryset):
        if self.value() == "no":
            return queryset.filter(
                letter_created_by__isnull=True,
            )
        elif self.value() == "yes":
            return queryset.exclude(
                letter_created_by__isnull=True,
            )
        else:
            return queryset


class VerifiedEmailUserFilter(admin.SimpleListFilter):
    title = _("Verified email")
    parameter_name = "verified_email_user"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(
                emailaddress__verified=True,
            )
        elif self.value() == "no":
            return queryset.exclude(
                emailaddress__verified=True,
            )
        else:
            return queryset


class MyUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User


class MyUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User

    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages["duplicate_username"])


@admin.register(User)
class UserAdmin(AdminImageMixin, AuthUserAdmin):
    form = MyUserChangeForm
    add_form = MyUserCreationForm
    fieldsets = list(AuthUserAdmin.fieldsets) + [
        (
            _("Notifications"),
            {
                "fields": (
                    "notify_new_case",
                    "notify_unassigned_letter",
                    "notify_old_cases",
                )
            },
        ),
        (
            _("Avatar"),
            {"fields": ("picture",)},
        ),
    ]
    date_hierarchy = "date_joined"
    list_display = (
        "id",
        "username",
        "first_name",
        "last_name",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "last_login",
        "codename",
        "notify_new_case",
        "notify_unassigned_letter",
        "notify_old_cases",
        "must_change_password",
    )
    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
    )
    list_filter = (
        "is_superuser",
        "is_staff",
        "is_active",
        VerifiedEmailUserFilter,
        IsSpamUserFilter,
        NoLoginUserFilter,
        HasCasesUserFilter,
        HasLettersUserFilter,
        "notify_new_case",
        "notify_unassigned_letter",
        "notify_old_cases",
        "groups",
    )
    actions = [
        "delete_selected",
        "force_password_change",
    ]

    def response_action(self, request, queryset):
        # Admin has 2 action selects: action (top) and action2 (bottom).
        action = request.POST.get("action") or request.POST.get("action2")

        # Only intercept deletes; let other actions run normally.
        if action != "delete_selected":
            return super().response_action(request, queryset)

        # --- delete-only override logic below ---
        selected = request.POST.getlist(helpers.ACTION_CHECKBOX_NAME)
        selected_qs = self.get_queryset(request).filter(pk__in=selected)
        case_msg, letter_msg = "", ""
        if selected_qs.filter(
            case_client__isnull=False,
            case_created__isnull=True,
            case_modified__isnull=True,
        ).exists():
            excluded_list = (
                selected_qs.filter(
                    case_client__isnull=False,
                    case_created__isnull=True,
                    case_modified__isnull=True,
                )
                .distinct()
                .values_list("username", flat=True)
            )
            case_msg = _(
                "Users with cases can be deleted with user form only: "
            ) + ", ".join(excluded_list)
            selected_qs = selected_qs.exclude(
                case_client__isnull=False,
                case_created__isnull=True,
                case_modified__isnull=True,
            )
        if selected_qs.filter(letter_created_by__isnull=False).exists():
            excluded_list = (
                selected_qs.filter(letter_created_by__isnull=False)
                .distinct()
                .values_list("username", flat=True)
            )
            letter_msg = _(
                "Users with letters can be deleted with user form only: "
            ) + ", ".join(excluded_list)
            selected_qs = selected_qs.exclude(letter_created_by__isnull=False)
        if case_msg or letter_msg:
            self.message_user(request, case_msg + "\n \n" + letter_msg)
        if selected_qs.exists():
            return super().response_action(request, selected_qs)
        else:
            self.message_user(
                request,
                _("No users to delete."),
            )
            return None

    @admin.action(description=_("Force password change on next login"))
    def force_password_change(self, request, queryset):
        # Only update rows that are not already marked (nice for accurate count)
        qs = queryset.exclude(must_change_password=True)
        updated = qs.update(must_change_password=True)

        messages.success(
            request, _(f"Marked {updated} user(s) to change password on next login.")
        )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Admin for User Profiles
    """

    list_display = (
        "pk",
        "user",
        "description",
        "www",
        "event_reminder_time",
    )
    list_filter = ("event_reminder_time",)
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "description",
        "www",
    )
    actions = None
