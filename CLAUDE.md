# Poradnia - Development Guide

Polish civic legal advice case management system built with Django.

## Architecture

- **Backend:** Django 5.2.11, Python 3.13
- **Database:** MySQL 8.0.36 (runs in Docker, exposed on `127.0.0.1:3306`)
- **Frontend:** Gulp + Sass + Bootstrap 3, built via Docker `gulp` service
- **Auth:** django-allauth with MFA, Google OAuth, django-guardian (object-level perms)

## Environment Setup

The `.claude/scripts/setup.sh` hook runs automatically on session start. It:
1. Starts Docker daemon and configures proxy if needed
2. Installs Python 3.13 via `uv` and creates venv at `/opt/poradnia-venv`
3. Installs all Python dependencies
4. Starts MySQL in Docker
5. Runs Django migrations

### Manual activation

```bash
source /opt/poradnia-venv/bin/activate
export DATABASE_URL="mysql://root:password@127.0.0.1:3306/poradnia"
export DJANGO_SETTINGS_MODULE="config.settings.local"
export GOOGLE_CLIENT_ID="" GOOGLE_CLIENT_SECRET=""
export ROSETTA_AZURE_CLIENT_SECRET="" TURNSTILE_SITE_KEY="" TURNSTILE_SECRET_KEY=""
export MY_INTERNAL_IP="" NGROK_URL="http://localhost"
export LETTER_RECEIVE_SECRET="dev_letter_receive_very_secret"
export LETTER_RECEIVE_WHITELISTED_ADDRESS="porady@porady.siecobywatelska.pl,porady@dev.porady.siecobywatelska.pl"
export APP_MODE="DEV" E2E_MFA_BYPASS_SECRET="supersecret-123"
export DJANGO_EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend"
export DJANGO_DEFAULT_FROM_EMAIL="poradnia_dev <noreply@dev.porady.siecobywatelska.pl>"
export DJANGO_RICH_TEXT_ENABLED="False"
```

## Running Tests

```bash
# Unit tests (288 tests)
python manage.py test --keepdb --verbosity=2

# Specific app
python manage.py test poradnia.cases --keepdb --verbosity=2

# Migration check
python manage.py makemigrations --check
```

## Key Directories

- `poradnia/` - Django apps (cases, letters, events, users, advicer, judgements, etc.)
- `config/settings/` - Django settings (common.py, local.py, production.py)
- `config/urls.py` - URL routing
- `requirements/` - Python deps (base.txt, dev.txt, production.txt)
- `tests/` - Cypress E2E tests
- `.contrib/docker/` - Dockerfiles

## Django Apps

| App | Purpose |
|-----|---------|
| `cases` | Case management (largest, ~25k lines of tests) |
| `letters` | Correspondence/email handling |
| `events` | Event tracking and reminders |
| `users` | Custom user model, profiles |
| `advicer` | Advisor/expert consultations |
| `judgements` | Court judgement tracking |
| `records` | Record management |
| `keys` | API key management |
| `navsearch` | Navigation search |
| `tasty_feedback` | User feedback |
| `teryt` | Polish territorial data (TERYT) |
