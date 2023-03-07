from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from sorl.thumbnail.admin import AdminImageMixin

from .models import Profile, User


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
            {"fields": ("notify_new_case", "notify_unassigned_letter")},
        )
    ]
    list_display = (
        "pk",
        "username",
        "first_name",
        "last_name",
        "email",
        "is_staff",
        "is_active",
        "codename",
        "notify_new_case",
        "notify_unassigned_letter",
    )
    list_filter = (
        "is_staff",
        "is_active",
        "codename",
        "notify_new_case",
        "notify_unassigned_letter",
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
