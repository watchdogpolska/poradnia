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

# The "gw" nginx in front of this app unconditionally sets X-Real-IP to the
# real caller's address (unspoofable by the client) - REMOTE_ADDR as seen by
# Django is just the app-nginx's own connecting IP, the same for every
# request. Without this, allauth's rate limiting (login, signup, password
# reset, account activation) would key off that constant value instead of
# the real client. Only set in production - dev/tests don't sit behind that
# proxy, so the header would be absent and allauth would raise PermissionDenied.
ALLAUTH_TRUSTED_CLIENT_IP_HEADER = "X-Real-IP"

# CELERY PRODUCTION SETTINGS
# Production-specific Celery configuration with enhanced monitoring and reliability
CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL", default="amqp://poradnia:password@rabbitmq:5672//"
)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="django-db")

# Production-specific performance optimizations
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = env.int(
    "CELERY_BROKER_CONNECTION_MAX_RETRIES", default=None
)
CELERY_BROKER_CONNECTION_TIMEOUT = env.int(
    "CELERY_BROKER_CONNECTION_TIMEOUT", default=15
)

# Worker monitoring and health checks
CELERY_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True
