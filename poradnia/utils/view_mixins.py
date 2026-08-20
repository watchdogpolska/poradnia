"""Local replacements for django-braces view/form mixins (unmaintained,
see requirements/base.txt).

Kept separate from poradnia.utils.mixins: that module is imported by
several apps' models.py (for queryset mixins), and importing
django.contrib.auth.views this early triggers get_user_model() before
the app registry is ready.
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.utils.encoding import force_str


class SelectRelatedMixin:
    select_related = None

    def get_queryset(self):
        if not self.select_related:
            raise ImproperlyConfigured(
                "{} is missing the select_related attribute.".format(
                    self.__class__.__name__
                )
            )
        return super().get_queryset().select_related(*self.select_related)


class PrefetchRelatedMixin:
    prefetch_related = None

    def get_queryset(self):
        if not self.prefetch_related:
            raise ImproperlyConfigured(
                "{} is missing the prefetch_related attribute.".format(
                    self.__class__.__name__
                )
            )
        return super().get_queryset().prefetch_related(*self.prefetch_related)


class SetHeadlineMixin:
    headline = None

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["headline"] = self.get_headline()
        return kwargs

    def get_headline(self):
        if self.headline is None:
            raise ImproperlyConfigured(
                "{0} is missing the headline attribute. Define "
                "{0}.headline, or override {0}.get_headline().".format(
                    self.__class__.__name__
                )
            )
        return force_str(self.headline)


class UserFormKwargsMixin:
    """Passes request.user to the form as the "user" kwarg."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class FormValidMessageMixin:
    """Calls get_form_valid_message() and shows it via the messages
    framework once the form is valid."""

    def get_form_valid_message(self):
        raise ImproperlyConfigured(
            "{} is missing a get_form_valid_message() method.".format(
                self.__class__.__name__
            )
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, self.get_form_valid_message(), fail_silently=True
        )
        return response


class StaffuserRequiredMixin:
    """Requires request.user.is_staff. Mirrors django-braces'
    StaffuserRequiredMixin: if raise_exception is falsy (the default),
    always redirect anonymous *and* authenticated non-staff users to
    login; if truthy, raise PermissionDenied instead."""

    raise_exception = False
    login_url = None
    redirect_field_name = REDIRECT_FIELD_NAME

    def get_login_url(self):
        return force_str(self.login_url or settings.LOGIN_URL)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            if self.raise_exception:
                raise PermissionDenied
            return redirect_to_login(
                request.get_full_path(), self.get_login_url(), self.redirect_field_name
            )
        return super().dispatch(request, *args, **kwargs)


class UserKwargModelFormMixin:
    """Pops "user" out of the form kwargs (put there by
    UserFormKwargsMixin) and attaches it to the form instance."""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
