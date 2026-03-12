from allauth.mfa.models import Authenticator
from django.contrib import admin

# If allauth already registered it, unregister first
try:
    admin.site.unregister(Authenticator)
except admin.sites.NotRegistered:
    pass


@admin.register(Authenticator)
class AuthenticatorAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "type", "created_at", "last_used_at")
    list_select_related = ("user",)
    search_fields = ("user__email", "user__username")
    list_filter = ("type",)

    # Make everything read-only in the change form
    readonly_fields = [f.name for f in Authenticator._meta.fields]

    def has_add_permission(self, request):
        return False  # no manual creation

    def has_change_permission(self, request, obj=None):
        return False  # no edits (prevents secret tampering)

    def has_delete_permission(self, request, obj=None):
        # allow MFA reset only for superusers (adjust to your policy)
        return bool(request.user and request.user.is_superuser)
