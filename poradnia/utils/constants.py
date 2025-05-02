from django.utils.translation import gettext as _

NAME_MAX_LENGTH = 250

TURNSTILE_ERROR_MESSAGES = {
    "error_turnstile": _("Turnstile could not be verified."),
    "invalid_turnstile": _("Turnstile could not be verified."),
    "required": _("Please prove you are a human."),
}
