# -*- coding: utf-8 -*-
# flake8: noqa: F405
'''
Production Configurations
'''
import os
import raven
from dealer.auto import auto

from .common import *  # noqa

# SECRET KEY
SECRET_KEY = env.str('DJANGO_SECRET_KEY')
# END SECRET KEY

# SITE CONFIGURATION
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/1.6/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["*"]
# END SITE CONFIGURATION

# EMAIL
DEFAULT_FROM_EMAIL = env.str('DJANGO_DEFAULT_FROM_EMAIL',
                             'poradnia <noreply@porady.siecobywatelska.pl>')
EMAIL_SUBJECT_PREFIX = env.str('DJANGO_EMAIL_SUBJECT_PREFIX', '[poradnia] ')

EMAIL_CONFIG = env.email_url('EMAIL_URL', default='smtp://localhost:25')
vars().update(EMAIL_CONFIG)

SERVER_EMAIL = env.str('DJANGO_SERVER_EMAIL')
# END EMAIL

# TEMPLATE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
TEMPLATES[0]['OPTIONS']['loaders'] = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)
# END TEMPLATE CONFIGURATION

# Your production stuff: Below this line define 3rd party libary settings
# Ustaw wartość twojego DSN
RELEASE_ID = auto.revision
RAVEN_CONFIG = {
    'dsn': env.str('RAVEN_DSN', 'http://example.com'),
    'release': RELEASE_ID
}

INSTALLED_APPS += ('raven.contrib.django.raven_compat',)
MIDDLEWARE_CLASSES = (
    "raven.contrib.django.raven_compat.middleware.Sentry404CatchMiddleware",
) + MIDDLEWARE_CLASSES
CACHES = {
    'default': env.cache(),
}
