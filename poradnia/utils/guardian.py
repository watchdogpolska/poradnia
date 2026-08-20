from django.contrib.auth.views import redirect_to_login
from guardian.mixins import PermissionRequiredMixin


class RaisePermissionRequiredMixin(PermissionRequiredMixin):
    """Object-level permission check, replacing the version from the
    unmaintained atom/django-braces combination: redirect anonymous
    users to login, raise PermissionDenied for authenticated users
    lacking the permission."""

    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(
                request.get_full_path(), self.login_url, self.redirect_field_name
            )
        return super().dispatch(request, *args, **kwargs)
