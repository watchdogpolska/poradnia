"""
Django settings for poradnia project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

from django.utils.translation import ugettext_lazy as _
import environ

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
    "tinymce",
    "flatpages_tinymce",
    "tinycontent",
    "sorl.thumbnail",
    "atom",
    "import_export",
    "django_filters",
    "bootstrap_pagination",
    "github_revision",
    "mptt",
    "teryt_tree",
    "antispam",
    "antispam.honeypot",
)

# Apps specific for this project go here.
LOCAL_APPS = (
    "poradnia.users",  # custom users app
    "poradnia.keys",
    "poradnia.cases",
    "poradnia.letters",
    "poradnia.records",
    "poradnia.events",
    "poradnia.stats",
    "poradnia.advicer",
    "poradnia.feedback_custom",
    "poradnia.tasty_feedback",
    "poradnia.navsearch",
    "poradnia.judgements",
    "poradnia.teryt"
    # Your stuff: custom apps go here
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
# END APP CONFIGURATION
INSTALLED_APPS = LOCAL_APPS + THIRD_PARTY_APPS + DJANGO_APPS

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
ADMINS = (
    ("Adam Dobrawy", "adam.dobrawy@siecobywatelska.pl"),
    ("Marcin Bójko", "marcin.bojko@siecobywatelska.pl"),
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS
# END MANAGER CONFIGURATION

# DATABASE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {"default": env.db(default="mysql:///porady")}

DATABASES["default"]["TEST"] = {
    "CHARSET": "utf8mb4",
    "COLLATION": "utf8mb4_unicode_520_ci",
}
DATABASES["default"]["CHARSET"] = "utf8mb4"

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

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (str(APPS_DIR.path("static")),)

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
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
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        }
    },
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        }
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

PORADNIA_EMAIL_OUTPUT = "sprawa-%(id)s@porady.siecobywatelska.pl"
PORADNIA_EMAIL_INPUT = r"sprawa-(?P<pk>\d+)@porady.siecobywatelska.pl"
ATOMIC_REQUESTS = True

TINYMCE_DEFAULT_CONFIG = {"theme": "advanced"}

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

STAT_METRICS = {
    "cases.count": "poradnia.cases.metric.cases_count",
    "cases.free": "poradnia.cases.metric.cases_free",
    "cases.assigned": "poradnia.cases.metric.cases_assigned",
    "cases.closed": "poradnia.cases.metric.cases_closed",
    "cases.monthly": "poradnia.cases.metric.cases_monthly",
    "users.total": "poradnia.users.metric.users_total",
    "users.monthly": "poradnia.users.metric.users_monthly",
    "users.active": "poradnia.users.metric.users_active",
    "users.active.staff": "poradnia.users.metric.users_active_staff",
    "letters.documents_written_for_clients": "poradnia.letters.metric.documents_written_for_clients",
    "letters.letter.month": "poradnia.letters.metric.letter_month",
    "letters.letter.staff.email": "poradnia.letters.metric.letter_staff_email",
    "letters.letter.staff.www": "poradnia.letters.metric.letter_staff_www",
    "letters.letter.total": "poradnia.letters.metric.letter_total",
    "letters.letter.user.email": "poradnia.letters.metric.letter_user_email",
    "letters.letter.user.www": "poradnia.letters.metric.letter_user_www",
}

FILE_UPLOAD_PERMISSIONS = 0o644

# Enable rich text formatting. Reverts to legacy plain text display when disabled.
RICH_TEXT_ENABLED = env.bool("DJANGO_RICH_TEXT_ENABLED", True)

# Django-GitHub-Revision
GITHUB_REVISION_REPO_URL = "https://github.com/watchdogpolska/poradnia"

LETTER_RECEIVE_SECRET = "xxxxxxxxx"
