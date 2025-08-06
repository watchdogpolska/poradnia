# flake8: noqa: F405
"""
Production Configurations
"""
import sentry_sdk
from dealer.auto import auto
from sentry_sdk.integrations.django import DjangoIntegration

from .common import *  # noqa

# SECRET KEY
SECRET_KEY = env.str("DJANGO_SECRET_KEY")
# END SECRET KEY

# TEMPLATE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
TEMPLATES[0]["OPTIONS"]["loaders"] = (
    (
        "django.template.loaders.cached.Loader",
        (
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ),
    ),
)
# END TEMPLATE CONFIGURATION

# Your production stuff: Below this line define 3rd party libary settings
# Ustaw wartość twojego DSN
REVISION_ID = auto.revision

sentry_sdk.init(
    dsn=env.str("RAVEN_DSN", "http://example.com"),
    release=REVISION_ID,
    integrations=[DjangoIntegration()],
)

CACHES = {"default": env.cache()}

ALLOWED_HOSTS = env.str("DJANGO_ALLOWED_HOSTS", default="localhost,").split(",")

CSRF_TRUSTED_ORIGINS = env.str(
    "DJANGO_CSRF_TRUSTED_ORIGINS", default="http://localhost,"
).split(",")
CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=True)
CSRF_COOKIE_DOMAIN = env.str("DJANGO_CSRF_COOKIE_DOMAIN", default="")
CSRF_COOKIE_SAMESITE = env.str("DJANGO_CSRF_COOKIE_SAMESITE", default="Strict")
