from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import ugettext_lazy as _
from sorl.thumbnail.admin import AdminImageMixin

from .models import User


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
