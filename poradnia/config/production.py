# -*- coding: utf-8 -*-
'''
Production Configurations
'''
from .common import *  # noqa
# SECRET KEY
SECRET_KEY = env('SECRET_KEY')
# END SECRET KEY

# SITE CONFIGURATION
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/1.6/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["*"]
# END SITE CONFIGURATION

# EMAIL
EMAIL_BACKEND = env.email_url(default='consolemail://')
DEFAULT_FROM_EMAIL = env(env='DEFAULT_FROM_EMAIL',
                         default='poradnia <noreply@porady.siecobywatelska.pl>')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_PORT = env.int('EMAIL_PORT')
EMAIL_SUBJECT_PREFIX = env('EMAIL_SUBJECT_PREFIX', default='[poradnia] ')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', defualt=True)
SERVER_EMAIL = EMAIL_HOST_USER
# END EMAIL

# TEMPLATE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)
# END TEMPLATE CONFIGURATION

# Your production stuff: Below this line define 3rd party libary settings
# Ustaw wartość twojego DSN
RAVEN_CONFIG = {
    'dsn': environ.get('RAVEN_DSN', 'http://example.com'),
}

INSTALLED_APPS += ('raven.contrib.django.raven_compat',)
MIDDLEWARE_CLASSES = (
    "raven.contrib.django.raven_compat.middleware.Sentry404CatchMiddleware",
) + MIDDLEWARE_CLASSES
CACHES = {
    'default': env.cache(),
}
