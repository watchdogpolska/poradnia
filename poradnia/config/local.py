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

# django-debug-toolbar
MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
INSTALLED_APPS += ('debug_toolbar', 'django_extensions', 'autofixture',)

INTERNAL_IPS = ('127.0.0.1', '10.0.2.2', )

DEBUG_TOOLBAR_CONFIG = {
    'DISABLE_PANELS': [
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ],
    'SHOW_TEMPLATE_CONTEXT': True,
}
