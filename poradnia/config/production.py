# -*- coding: utf-8 -*-
'''
Production Configurations
'''
from .common import *  # noqa
# SECRET KEY
SECRET_KEY = env.str('DJANGO_SECRET_KEY')
# END SECRET KEY

# SITE CONFIGURATION
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/1.6/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["*"]
# END SITE CONFIGURATION

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
    'dsn': env.str('RAVEN_DSN', 'http://example.com'),
}

INSTALLED_APPS += ('raven.contrib.django.raven_compat',)
MIDDLEWARE_CLASSES = (
    "raven.contrib.django.raven_compat.middleware.Sentry404CatchMiddleware",
) + MIDDLEWARE_CLASSES
CACHES = {
    'default': env.cache(),
}
