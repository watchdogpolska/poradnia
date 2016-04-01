# -*- coding: utf-8 -*-
'''
Local Configurations

- Runs in Debug mode
- Uses console backend for emails
- Use Django Debug Toolbar
'''
from .common import *  # noqa

# DEBUG
DEBUG = env('DEBUG', default=True)
TEMPLATE_DEBUG = DEBUG
# END DEBUG

# django-extensions

INSTALLED_APPS += ('django_extensions',)

# django-autofixture

INSTALLED_APPS += ('autofixture',)

# django-debug-toolbar

INSTALLED_APPS += ('debug_toolbar',)

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]


INTERNAL_IPS = ('127.0.0.1', '10.0.2.2', )

DEBUG_TOOLBAR_CONFIG = {
    'DISABLE_PANELS': [
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ],
    'SHOW_TEMPLATE_CONTEXT': True,
}
