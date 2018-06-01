#!/usr/bin/env bash
set -e

python manage.py collectstatic --no-input
python manage.py migrate;

exec "$@"
