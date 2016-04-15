from django.conf import settings


HOSTS = getattr(settings, 'AUTH_IMAP_HOSTS', {})
