# -*- coding: utf-8 -*-
"""
Django settings for poradnia project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""
from __future__ import absolute_import, unicode_literals

import environ
from django.utils.translation import ugettext_lazy as _

ROOT_DIR = environ.Path(__file__) - 3

APPS_DIR = ROOT_DIR.path('poradnia')

env = environ.Env()

# APP CONFIGURATION
DJANGO_APPS = (
    # Default Django apps:
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.flatpages',
    # Useful template tags:
    'django.contrib.humanize',

    # Admin
    'django.contrib.admin',
)
THIRD_PARTY_APPS = (
    'crispy_forms',  # Form layouts
    'allauth',  # registration
    'allauth.account',  # registration
    'allauth.socialaccount',  # registration
    'guardian',
    'django_mailbox',
    'autocomplete_light',
    'tinymce',
    'flatpages_tinymce',
    'tinycontent',
    'sorl.thumbnail',
    'atom',
)

# Apps specific for this project go here.
LOCAL_APPS = (
    'users',  # custom users app
    'keys',
    'cases',
    'letters',
    'records',
    'events',
    'advicer',
    'feedback_custom',
    'tasty_feedback',
    'bootstrap_pagination',
    'navsearch'
    # Your stuff: custom apps go here
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
# END APP CONFIGURATION
INSTALLED_APPS = LOCAL_APPS + THIRD_PARTY_APPS + DJANGO_APPS

# MIDDLEWARE CONFIGURATION
MIDDLEWARE_CLASSES = (
    # 'django.middleware.locale.LocaleMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
# END MIDDLEWARE CONFIGURATION

# MIGRATIONS CONFIGURATION
MIGRATION_MODULES = {
    'sites': 'contrib.sites.migrations'
}
# END MIGRATIONS CONFIGURATION

# DEBUG
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool('DJANGO_DEBUG', default=False)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
TEMPLATE_DEBUG = DEBUG
# END DEBUG

# SECRET CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Note: This key only used for development and testing.
#       In production, this is changed to a values.SecretValue() setting
SECRET_KEY = env.str("SECRET_KEY", default="CHANGEME!!!")
# END SECRET CONFIGURATION

# FIXTURE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FIXTURE_DIRS
FIXTURE_DIRS = (
    str(APPS_DIR.path('fixtures')),
)
# END FIXTURE CONFIGURATION

# EMAIL
EMAIL_BACKEND = env.str('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env.str('DJANGO_EMAIL_HOST', '')
EMAIL_HOST_PASSWORD = env.str('DJANGO_EMAIL_HOST_PASSWORD', '')
EMAIL_HOST_USER = env.str('DJANGO_EMAIL_HOST_USER', '')
EMAIL_PORT = env.str('DJANGO_EMAIL_PORT', '')

DEFAULT_FROM_EMAIL = env.str('DJANGO_DEFAULT_FROM_EMAIL',
                             'poradnia <noreply@porady.siecobywatelska.pl>')
EMAIL_SUBJECT_PREFIX = env.str('DJANGO_EMAIL_SUBJECT_PREFIX', '[poradnia] ')
EMAIL_USE_TLS = env.bool('DJANGO_EMAIL_USE_TLS', True)
SERVER_EMAIL = EMAIL_HOST_USER
# END EMAIL

# MANAGER CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = (
    ("""Adam Dobrawy""", 'naczelnik@jawnosc.tk'),
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS
# END MANAGER CONFIGURATION

# DATABASE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': env.db(),
}
# END DATABASE CONFIGURATION

# CACHING
# Do this here because thanks to django-pylibmc-sasl and pylibmc
# memcacheify (used on heroku) is painful to install on windows.
CACHES = {
    'default': env.cache_url(default='locmemcache://')
}
# END CACHING

# GENERAL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#time-zone
TIME_ZONE = 'Europe/Warsaw'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'pl'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# END GENERAL CONFIGURATION

# TEMPLATE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
    # Your stuff: custom template context processers go here
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
TEMPLATE_DIRS = (
    str(APPS_DIR.path('templates')),
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

# See: http://django-crispy-forms.readthedocs.org/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = 'bootstrap3'
# END TEMPLATE CONFIGURATION

# STATIC FILE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-ROOT_DIR
STATIC_ROOT = str(APPS_DIR.path('staticfiles'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    str(APPS_DIR.path('static')),
)

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
# END STATIC FILE CONFIGURATION

# MEDIA CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-ROOT_DIR
MEDIA_ROOT = str(APPS_DIR.path('media'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'
# END MEDIA CONFIGURATION

# URL Configuration
ROOT_URLCONF = 'urls'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'wsgi.application'
# End URL Configuration

# AUTHENTICATION CONFIGURATION
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    'guardian.backends.ObjectPermissionBackend',
    "allauth.account.auth_backends.AuthenticationBackend",
)

# Some really nice defaults
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "optional"
# END AUTHENTICATION CONFIGURATION

# Custom user app defaults
# Select the correct user model
AUTH_USER_MODEL = "users.User"
ACCOUNT_SIGNUP_FORM_CLASS = 'users.forms.SignupForm'
ACCOUNT_FORMS = {'login': 'users.login_form.CustomLoginForm'}
LOGIN_REDIRECT_URL = "home"
LOGIN_URL = "account_login"
# END Custom user app defaults

# SLUGLIFIER
AUTOSLUG_SLUGIFY_FUNCTION = "slugify.slugify"
# END SLUGLIFIER

# LOGGING CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
# END LOGGING CONFIGURATION

# Your common stuff: Below this line define 3rd party library settings
# Guardian settings
ANONYMOUS_USER_ID = -1
GUARDIAN_MONKEY_PATCH = False

LANGUAGES = (
  ('pl', _('Polish')),
  ('en', _('English')),
)

LOCALE_PATHS = (str(APPS_DIR.path('templates/locale')),)

PORADNIA_EMAIL_OUTPUT = "sprawa-%(id)s@porady.siecobywatelska.pl"
PORADNIA_EMAIL_INPUT = "^sprawa-(?P<pk>\d+)@porady.siecobywatelska.pl$"
ATOMIC_REQUESTS = True  # Why?

TINYMCE_DEFAULT_CONFIG = {
    'theme': "advanced",
}

AVATAR_GRAVATAR_DEFAULT = 'retro'
FEEDBACK_FILTER = 'feedback_custom.filters.AtomFeedbackFilter'
FEEDBACK_FORM_SUBMIT = 'feedback_custom.forms.FeedbackForm'
FEEDBACK_GITHUB_REPO = 'https://github.com/watchdogpolska/poradnia'

DJANGO_MAILBOX_STORE_ORIGINAL_MESSAGE = True

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

EMAIL_BACKEND = env.str('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
