# flake8: noqa: F405
"""
Local Configurations

- Runs in Debug mode
- Uses console backend for emails
- Use Django Debug Toolbar
"""
import sys

from .common import *  # noqa

# DEBUG
DEBUG = env("DEBUG", default=True)
TESTING = (len(sys.argv) > 1 and sys.argv[1] == "test") or env("TEST", default=False)
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG
# END DEBUG

# django-extensions

INSTALLED_APPS += ("django_extensions",)

# django-debug-toolbar

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

MY_INTERNAL_IP = env("MY_INTERNAL_IP", default="")
INTERNAL_IPS = ("127.0.0.1", "10.0.2.2", MY_INTERNAL_IP)

DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
    "SHOW_TOOLBAR_CALLBACK": lambda x: not TESTING,
    "SHOW_TEMPLATE_CONTEXT": True,
}
