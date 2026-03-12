from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.contrib import admin


def _readonly_all_fields(model):
    return [f.name for f in model._meta.fields]


# ---- SocialAccount ----------------------------------------------------------

try:
    admin.site.unregister(SocialAccount)
except admin.sites.NotRegistered:
    pass


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "provider", "uid", "date_joined", "last_login")
    list_select_related = ("user",)
    search_fields = ("user__email", "user__username", "uid")
    list_filter = ("provider",)

    readonly_fields = _readonly_all_fields(SocialAccount)

    def has_add_permission(self, request):
        return False  # no manual creation

    def has_change_permission(self, request, obj=None):
        return False  # no edits

    def has_delete_permission(self, request, obj=None):
        # allow unlink/reset only for superusers (adjust if needed)
        return bool(request.user and request.user.is_superuser)


# ---- SocialToken (usually best to hide or read-only+delete) ------------------

try:
    admin.site.unregister(SocialToken)
except admin.sites.NotRegistered:
    pass


@admin.register(SocialToken)
class SocialTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "account", "app", "expires_at")
    search_fields = ("account__user__email", "account__uid")
    list_filter = ("app__provider",)

    readonly_fields = _readonly_all_fields(SocialToken)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return bool(request.user and request.user.is_superuser)


# ---- SocialApp (credentials) ------------------------------------------------
# Strongly recommended: superuser-only, and usually editable only by superusers.

try:
    admin.site.unregister(SocialApp)
except admin.sites.NotRegistered:
    pass


@admin.register(SocialApp)
class SocialAppAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "provider", "client_id")
    search_fields = ("name", "provider", "client_id")
    list_filter = ("provider",)

    readonly_fields = _readonly_all_fields(SocialApp)

    def has_module_permission(self, request):
        return bool(request.user and request.user.is_superuser)

    def has_view_permission(self, request, obj=None):
        return bool(request.user and request.user.is_superuser)

    def has_add_permission(self, request):
        return bool(request.user and request.user.is_superuser)

    def has_change_permission(self, request, obj=None):
        return bool(request.user and request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        return bool(request.user and request.user.is_superuser)
