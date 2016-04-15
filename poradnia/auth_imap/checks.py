from django.core.checks import register, Warning
from django.conf import settings


@register()
def check_settings(app_configs=None, **kwargs):
    """ Check that settings are implemented properly
    :param app_configs: a list of apps to be checks or None for all
    :param kwargs: keyword arguments
    :return: a list of errors
    """
    checks = []
    if 'auth_imap.backends.IMAPAuthBackend' not in settings.AUTHENTICATION_BACKENDS:
        msg = ("Djangoa-Auth-IMAP backend is not configured. You should add " +
               "'auth-imap.backends.IMAPAuthBackend' to AUTHENTICATION_BACKENDS.")
        checks.append(Warning(msg, id='auth_imap.W001'))

    if not getattr(settings, 'AUTH_IMAP_HOSTS', None):
        msg = ("Djangoa-Auth-IMAP backend is not configured. You should add hosts settings as " +
               "AUTH_IMAP_HOSTS.")
        checks.append(Warning(msg, id='auth_imap.W002'))
    return checks
