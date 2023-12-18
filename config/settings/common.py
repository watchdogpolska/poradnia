"""
Django settings for poradnia project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import environ
from django.utils.translation import gettext_lazy as _

ROOT_DIR = environ.Path(__file__) - 3

APPS_DIR = ROOT_DIR.path("poradnia")

env = environ.Env()

# APP CONFIGURATION
DJANGO_APPS = (
    # Default Django apps:
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.flatpages",
    # Useful template tags:
    "django.contrib.humanize",
    # Admin
    "django.contrib.admin",
)
THIRD_PARTY_APPS = (
    "crispy_forms",  # Form layouts
    "allauth",  # registration
    "allauth.account",  # registration
    "allauth.socialaccount",  # registration
    "guardian",
    "django_mailbox",
    "dal",
    "dal_select2",
    "tinycontent",
    "sorl.thumbnail",
    "atom",
    "django_filters",
    "bootstrap_pagination",
    "github_revision",
    "mptt",
    "teryt_tree",
    "antispam",
    "antispam.honeypot",
    "tinymce",
    "ajax_datatable",
    "rosetta",
)

# Apps specific for this project go here.
LOCAL_APPS = (
    "poradnia.users",  # custom users app
    "poradnia.keys",
    "poradnia.cases",
    "poradnia.letters",
    "poradnia.records",
    "poradnia.events",
    "poradnia.advicer",
    "poradnia.feedback_custom",
    "poradnia.tasty_feedback",
    "poradnia.navsearch",
    "poradnia.judgements",
    "poradnia.teryt",
    "poradnia.utils"
    # Your stuff: custom apps go here
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
# END APP CONFIGURATION
INSTALLED_APPS = THIRD_PARTY_APPS + LOCAL_APPS + DJANGO_APPS

# MIDDLEWARE CONFIGURATION
MIDDLEWARE = (
    # 'django.middleware.locale.LocaleMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)
# END MIDDLEWARE CONFIGURATION

# SITE CONFIGURATION
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/1.6/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["*"]
# END SITE CONFIGURATION

# MIGRATIONS CONFIGURATION
MIGRATION_MODULES = {"sites": "poradnia.contrib.sites.migrations"}
# END MIGRATIONS CONFIGURATION

# DEBUG
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", default=False)

# SECRET CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Note: This key only used for development and testing.
#       In production, this is changed to a values.SecretValue() setting
SECRET_KEY = env.str("SECRET_KEY", default="CHANGEME!!!")
# END SECRET CONFIGURATION

# FIXTURE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FIXTURE_DIRS
FIXTURE_DIRS = (str(APPS_DIR.path("fixtures")),)
# END FIXTURE CONFIGURATION

# EMAIL
EMAIL_BACKEND = env.str(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = env.str("DJANGO_EMAIL_HOST", "")
EMAIL_HOST_PASSWORD = env.str("DJANGO_EMAIL_HOST_PASSWORD", "")
EMAIL_HOST_USER = env.str("DJANGO_EMAIL_HOST_USER", "")
EMAIL_PORT = env.str("DJANGO_EMAIL_PORT", "")

DEFAULT_FROM_EMAIL = env.str(
    "DJANGO_DEFAULT_FROM_EMAIL", "poradnia <noreply@porady.siecobywatelska.pl>"
)
EMAIL_SUBJECT_PREFIX = env.str("DJANGO_EMAIL_SUBJECT_PREFIX", "[poradnia] ")
EMAIL_USE_TLS = env.bool("DJANGO_EMAIL_USE_TLS", True)
SERVER_EMAIL = EMAIL_HOST_USER
# END EMAIL

# MANAGER CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [
    ("Admninistratorzy", "admins@siecobywatelska.pl"),
]

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS
# END MANAGER CONFIGURATION

# DATABASE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {"default": env.db(default="mysql:///porady")}

DATABASES["default"]["TEST"] = {
    #    "CHARSET": "utf8mb4",
    #    "COLLATION": "utf8mb4_unicode_520_ci",
    "CHARSET": "utf8",
    "COLLATION": "utf8_polish_ci",
}
# DATABASES["default"]["CHARSET"] = "utf8mb4"
DATABASES["default"]["CHARSET"] = "utf"

# END DATABASE CONFIGURATION

# CACHING
# Do this here because thanks to django-pylibmc-sasl and pylibmc
# memcacheify (used on heroku) is painful to install on windows.
CACHES = {"default": env.cache_url(default="locmemcache://")}
# END CACHING

# GENERAL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#time-zone
TIME_ZONE = "Europe/Warsaw"

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "pl"

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# END GENERAL CONFIGURATION


# See: http://django-crispy-forms.readthedocs.org/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap3"
# END TEMPLATE CONFIGURATION

# STATIC FILE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-ROOT_DIR
STATIC_ROOT = str(ROOT_DIR.path("staticfiles"))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"

# See: https://docs.djangoproject.com/en/dev/ref/
#      contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (str(APPS_DIR.path("static")),)

# See: https://docs.djangoproject.com/en/dev/ref/
#      contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)
# END STATIC FILE CONFIGURATION

# MEDIA CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-ROOT_DIR
MEDIA_ROOT = str(APPS_DIR.path("media"))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"
# END MEDIA CONFIGURATION

# URL Configuration
ROOT_URLCONF = "config.urls"

# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "config.wsgi.application"
# End URL Configuration

# AUTHENTICATION CONFIGURATION
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
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
ACCOUNT_SIGNUP_FORM_CLASS = "poradnia.users.forms.SignupForm"
ACCOUNT_FORMS = {"login": "poradnia.users.login_form.CustomLoginForm"}
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
#
# TODO add proper file logging configuration when loggers added to code
#   as for now all stdout and stderr captured by gunicorn logs
LOG_FILE_ENV = env("LOG_FILE_ENV", default="logs/poradnia.log")
LOG_FILE = str(ROOT_DIR(LOG_FILE_ENV))
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    # "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "app",
        },
        "file": {
            # "level": "INFO",
            "class": "logging.FileHandler",
            "filename": LOG_FILE,
            "formatter": "app",
        },
    },
    "loggers": {
        # "django.request": {"handlers": [], "level": "ERROR", "propagate": True},
        "": {"handlers": ["file", "console"], "level": "INFO", "propagate": True},
        "feder.letters.models": {
            "handlers": ["console"] if "test" not in environ.sys.argv else [],
            "level": "INFO",
        },
    },
    "formatters": {
        "app": {
            "format": (
                "%(asctime)s [%(levelname)-7s] "
                # "(%(module)s.%(funcName)s) %(message)s"
                "(%(pathname)s:%(lineno)s) %(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
}
# END LOGGING CONFIGURATION

# Your common stuff: Below this line define 3rd party library settings
# Guardian settings
ANONYMOUS_USER_ID = -1
ANONYMOUS_USER_NAME = "AnonymousUser"
GUARDIAN_MONKEY_PATCH = False

LANGUAGES = (("pl", _("Polish")), ("en", _("English")))

LOCALE_PATHS = (str(APPS_DIR.path("templates/locale")),)

# APP_MODE used to differentiate dev, demo and production environments
# use DEV, DEMO and PROD values in env variable APP_MODE
APP_MODE = env.str("APP_MODE", "DEMO")

PORADNIA_EMAIL_OUTPUT = "sprawa-%(id)s@porady.siecobywatelska.pl"
PORADNIA_EMAIL_INPUT = r"sprawa-(?P<pk>\d+)@porady.siecobywatelska.pl"
if APP_MODE == "DEV":
    PORADNIA_EMAIL_OUTPUT = "sprawa-%(id)s@dev.porady.siecobywatelska.pl"
    PORADNIA_EMAIL_INPUT = r"sprawa-(?P<pk>\d+)@dev.porady.siecobywatelska.pl"
elif APP_MODE == "DEMO":
    PORADNIA_EMAIL_OUTPUT = "sprawa-%(id)s@staging.porady.siecobywatelska.pl"
    PORADNIA_EMAIL_INPUT = r"sprawa-(?P<pk>\d+)@staging.porady.siecobywatelska.pl"

# Other Poradnia settings
ATOMIC_REQUESTS = True

AVATAR_GRAVATAR_DEFAULT = "retro"
FEEDBACK_FILTER = "poradnia.feedback_custom.filters.AtomFeedbackFilter"
FEEDBACK_FORM_SUBMIT = "poradnia.feedback_custom.forms.FeedbackForm"
FEEDBACK_GITHUB_REPO = "https://github.com/watchdogpolska/poradnia"

DJANGO_MAILBOX_STORE_ORIGINAL_MESSAGE = True

TEST_RUNNER = "django.test.runner.DiscoverRunner"

EMAIL_BACKEND = env.str(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(APPS_DIR.path("templates"))],
        "OPTIONS": {
            "context_processors": (
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ),
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            "debug": DEBUG,
            "libraries": {  # Adding this section should work around the issue.
                "staticfiles": "django.templatetags.static",
                "i18n": "django.templatetags.i18n",
            },
        },
    }
]
FILTERS_HELP_TEXT_FILTER = False

FILE_UPLOAD_PERMISSIONS = 0o644

# Enable rich text formatting. Reverts to legacy plain text display when disabled.
RICH_TEXT_ENABLED = env.bool("DJANGO_RICH_TEXT_ENABLED", True)

# Django-GitHub-Revision
GITHUB_REVISION_REPO_URL = "https://github.com/watchdogpolska/poradnia"

LETTER_RECEIVE_SECRET = env.str("LETTER_RECEIVE_SECRET", "")

LETTER_RECEIVE_WHITELISTED_ADDRESS = env.str(
    "LETTER_RECEIVE_WHITELISTED_ADDRESS", "porady@siecobywatelska.pl,"
).split(",")

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

TINYMCE_DEFAULT_CONFIG = {
    "theme": "silver",
    "height": 500,
    "menubar": True,
    "lineheight": 1,
    "plugins": "advlist,autolink,lists,link,image,charmap,print,preview,anchor,"
    "searchreplace,visualblocks,code,fullscreen,insertdatetime,media,table,paste,"
    "code,help,wordcount",
    "toolbar": "undo redo | formatselect | lineheight | fontsizeselect |"
    "bold italic backcolor | alignleft aligncenter "
    "alignright alignjustify | bullist numlist outdent indent | "
    "charmap | removeformat | help",
}


ROSETTA_SHOW_AT_ADMIN_PANEL = True

# Rosetta translation settings
ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS = True
ROSETTA_EXCLUDED_APPLICATIONS = (
    "django.contrib.admin",  # for some reason does not exclue admin app
    "django.contrib.auth",
    "constance",
    "allauth",
    "dal_select2",
    "django_tables2",
    "rosetta",
    "simple_history",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "django_filters",
    "vies",
)
AZURE_CLIENT_SECRET = env.str("ROSETTA_AZURE_CLIENT_SECRET", "")

# Send notifications to case or letter change/addition author
NOTIFY_AUTHOR = env.bool("NOTIFY_AUTHOR", True)

# The number of years after which cases will be listed to delete
YEARS_TO_STORE_CASES = env.int("YEARS_TO_STORE_CASES", 6)

BLEACH_ALLOWED_TAGS = {
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "code",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "strong",
    "em",
    "p",
    "ul",
    "ol",
    "i",
    "li",
    "br",
    "sub",
    "sup",
    "hr",
    "pre",
    "img",
}

BLEACH_ALLOWED_ATTRIBUTES = ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
    "abbr": ["title"],
    "acronym": ["title"],
    "img": ["alt", "src", "title"],
}
