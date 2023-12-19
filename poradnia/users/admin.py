from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from sorl.thumbnail.admin import AdminImageMixin

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
    list_display = (
        "pk",
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
    )
    list_filter = (
        "is_superuser",
        "is_staff",
        "is_active",
        IsSpamUserFilter,
        "notify_new_case",
        "notify_unassigned_letter",
        "notify_old_cases",
        "groups",
    )
    actions = None


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
