# -*- coding: utf-8 -*-
'''
Production Configurations

- Use djangosecure
- Use Amazon's S3 for storing static files and uploaded media
- Use sendgird to sendemails
- Use MEMCACHIER on Heroku
'''
from configurations import values
from .common import Common
from os import environ


class Production(Common):
    INSTALLED_APPS = Common.INSTALLED_APPS
    MIDDLEWARE_CLASSES = Common.MIDDLEWARE_CLASSES

    # This ensures that Django will be able to detect a secure connection
    # properly on Heroku.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # INSTALLED_APPS
    # END INSTALLED_APPS

    # SECRET KEY
    SECRET_KEY = values.SecretValue()
    # END SECRET KEY

    # django-secure
    INSTALLED_APPS += ("djangosecure", )
    # set this to 60 seconds and then to 518400 when you can prove it works
    # SECURE_HSTS_SECONDS = 60
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = values.BooleanValue(True)
    # SECURE_FRAME_DENY = values.BooleanValue(True)
    # SECURE_CONTENT_TYPE_NOSNIFF = values.BooleanValue(True)
    # SECURE_BROWSER_XSS_FILTER = values.BooleanValue(True)
    # SESSION_COOKIE_SECURE = values.BooleanValue(False)
    # SESSION_COOKIE_HTTPONLY = values.BooleanValue(True)
    # SECURE_SSL_REDIRECT = values.BooleanValue(True)
    # end django-secure

    # SITE CONFIGURATION
    # Hosts/domain names that are valid for this site
    # See https://docs.djangoproject.com/en/1.6/ref/settings/#allowed-hosts
    ALLOWED_HOSTS = ["*"]
    # END SITE CONFIGURATION

    INSTALLED_APPS += ("gunicorn", )

    # EMAIL
    DEFAULT_FROM_EMAIL = values.Value('poradnia <noreply@porady.siecobywatelska.pl>')
    EMAIL_HOST = values.Value('smtp.sendgrid.com')
    EMAIL_HOST_PASSWORD = values.SecretValue()
    EMAIL_HOST_USER = values.SecretValue()
    EMAIL_PORT = values.IntegerValue(587)
    EMAIL_SUBJECT_PREFIX = values.Value('[poradnia] ')
    EMAIL_USE_TLS = True
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

    # CACHING
    # Only do this here because thanks to django-pylibmc-sasl and pylibmc
    # memcacheify is painful to install on windows.
    try:
        # See: https://github.com/rdegges/django-heroku-memcacheify
        from memcacheify import memcacheify
        CACHES = memcacheify()
    except ImportError:
        CACHES = values.CacheURLValue(default="memcached://127.0.0.1:11211")
    # END CACHING

    # Your production stuff: Below this line define 3rd party libary settings
    # Ustaw wartość twojego DSN
    RAVEN_CONFIG = {
        'dsn': environ.get('RAVEN_DSN', 'http://example.com'),
    }

    INSTALLED_APPS += ('raven.contrib.django.raven_compat',)
    MIDDLEWARE_CLASSES = (
        "raven.contrib.django.raven_compat.middleware.Sentry404CatchMiddleware",
    ) + MIDDLEWARE_CLASSES
