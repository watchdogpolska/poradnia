# flake8: noqa: F405
"""
Local Configurations

- Runs in Debug mode
- Uses console backend for emails
- Use Django Debug Toolbar
"""
from .common import *  # noqa

# DEBUG
DEBUG = env("DEBUG", default=True)
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG
# END DEBUG

# django-extensions

INSTALLED_APPS += ("django_extensions",)

# django-debug-toolbar

if "test" not in sys.argv:
    INSTALLED_APPS += ("debug_toolbar",)
    MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)
    DEBUG_TOOLBAR_PANELS = [
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.templates.TemplatesPanel",
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.logging.LoggingPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
    ]
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TEMPLATE_CONTEXT": True,
        "SHOW_TOOLBAR_CALLBACK": lambda x: "test" not in sys.argv,
    }
    ROSETTA_EXCLUDED_APPLICATIONS += ("debug_toolbar",)

TURNSTILE_ENABLE = env("TURNSTILE_ENABLE", default=True)

MY_INTERNAL_IP = env("MY_INTERNAL_IP", default="")
INTERNAL_IPS = ("127.0.0.1", "10.0.2.2", MY_INTERNAL_IP)

DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
    "SHOW_TOOLBAR_CALLBACK": lambda x: not TESTING,
    "SHOW_TEMPLATE_CONTEXT": True,
}

ACCOUNT_EMAIL_VERIFICATION = env("ACCOUNT_EMAIL_VERIFICATION", default="mandatory")
CSRF_TRUSTED_ORIGINS = [
    "http://*",
    env("NGROK_URL", default="http://localhost").strip(),
]

# CELERY LOCAL SETTINGS
# Development-specific Celery configuration
CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL", default="amqp://poradnia:password@localhost:5672//"
)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="django-db")

# Enable task eager execution for development/testing
if TESTING:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_TASK_STORE_EAGER_RESULT = True
    CELERY_BROKER_URL = "memory://"
    CELERY_RESULT_BACKEND = "cache+memory://"
