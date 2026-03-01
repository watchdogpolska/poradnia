from __future__ import annotations

import logging

from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve, reverse

AUTH_METHODS_SESSION_KEY = "account_authentication_methods"


logger = logging.getLogger(__name__)


def _get_auth_method_types(request) -> set[str]:
    """
    allauth stores a list of dicts in session, e.g.:
      [{"method": "password"}, {"method": "totp"}]
    """
    methods = request.session.get(AUTH_METHODS_SESSION_KEY, []) or []
    out: set[str] = set()
    for m in methods:
        if isinstance(m, dict):
            t = m.get("method")
            if isinstance(t, str):
                out.add(t)
    return out


class EnforceStaffMfaOnPasswordLoginMiddleware:
    """
    Policy:
      - If user is staff/superuser AND session indicates password was used,
        require MFA completion (TOTP/recovery codes) before allowing access.
      - If user authenticated via social login only (e.g., Google),
        do NOT require allauth MFA.

    Notes:
      - Prevent redirect loops by exempting allauth account + mfa endpoints.
      - One can further scope enforcement to /admin/ only if desired.
    """

    # URL names we allow even if MFA not completed (avoid loops)
    EXEMPT_URL_NAMES: set[str] = {
        # core allauth
        "account_login",
        "account_logout",
        "account_signup",
        "account_reset_password",
        "account_reset_password_done",
        "account_reset_password_from_key",
        "account_reset_password_from_key_done",
        # allauth mfa
        "mfa_index",
        "mfa_authenticate",
        "mfa_reauthenticate",
        "mfa_activate_totp",
        "mfa_deactivate_totp",
        "mfa_generate_recovery_codes",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        path = request.path_info

        static_url = getattr(settings, "STATIC_URL", "/static/")
        media_url = getattr(settings, "MEDIA_URL", "/media/")

        # Only treat STATIC_URL / MEDIA_URL as path prefixes when they look like paths
        static_prefix = static_url if static_url.startswith("/") else "/static/"
        media_prefix = media_url if media_url.startswith("/") else "/media/"

        # Skip if user not authenticated
        # Only enforce for staff/superuser
        # Exempt static/media and exempt url names
        if (
            (not user or not user.is_authenticated)
            or not (user.is_staff or user.is_superuser)
            or path.startswith(static_prefix)
            or path.startswith(media_prefix)
            or path in ("/favicon.ico", "/robots.txt")
        ):
            return self.get_response(request)

        # Debug logging to help troubleshoot any issues with E2E bypass
        # logger.info(
        #     "E2E enabled=%s",
        #     getattr(settings, "E2E_MFA_BYPASS_ENABLED", None),
        # )
        # logger.info("E2E secret=%s", getattr(settings, "E2E_MFA_BYPASS_SECRET", None))
        # logger.info("E2E received cookies=%s", request.COOKIES.get("e2e_bypass_mfa"))

        # E2E tests bypass: if enabled and cookie matches secret, skip MFA enforcement.
        if getattr(settings, "E2E_MFA_BYPASS_ENABLED", False):
            secret = getattr(settings, "E2E_MFA_BYPASS_SECRET", "")
            if secret and request.COOKIES.get("e2e_bypass_mfa") == secret:
                return self.get_response(request)

        try:
            match = resolve(request.path_info)
            if match.url_name in self.EXEMPT_URL_NAMES:
                return self.get_response(request)
        except Exception:
            # If resolve fails for some reason, fall through to enforcement
            pass

        auth_method_types = _get_auth_method_types(request)

        # If the login did NOT involve a password (e.g. Google social login),
        # allow access without allauth MFA.
        if "password" not in auth_method_types and "socialaccount" in auth_method_types:
            return self.get_response(request)

        # If password was used, require MFA completion.
        # Depending on factors, session may record "totp" (and/or "recovery_codes").
        if "password" in auth_method_types:
            mfa_done = bool(
                auth_method_types.intersection({"totp", "recovery_codes", "mfa"})
            )
            if not mfa_done:
                logger.info(
                    "AUTH_METHODS: %s",
                    request.session.get("account_authentication_methods"),
                )
                logger.info("PATH: %s", request.path)
                return redirect(reverse("mfa_index"))

        return self.get_response(request)


class ForcePasswordChangeMiddleware:
    """
    Forces authenticated users with must_change_password=True
    to change their password before accessing the rest of the site.
    """

    ALLOWED_VIEWNAMES = {
        "account_change_password",
        "account_set_password",
        "account_logout",
        "account_login",
    }

    ALLOWED_PATH_PREFIXES = (
        settings.STATIC_URL,
        settings.MEDIA_URL,
        "/admin/login/",  # prevent admin login loop
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            if getattr(user, "must_change_password", False):

                # Allow static/media immediately
                if request.path.startswith(self.ALLOWED_PATH_PREFIXES):
                    return self.get_response(request)

                try:
                    match = resolve(request.path_info)
                    viewname = match.view_name
                except Exception:
                    viewname = None

                if viewname not in self.ALLOWED_VIEWNAMES:

                    # If user has no usable password (e.g. social-only account),
                    # send them to set_password instead of change_password
                    if not user.has_usable_password():
                        return redirect(reverse("account_set_password") + "?next=/")

                    return redirect(reverse("account_change_password") + "?next=/")

        return self.get_response(request)
