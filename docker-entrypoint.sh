#!/usr/bin/env bash
set -e

python manage.py collectstatic -l --no-input
./node_modules/.bin/gulp build;
python manage.py migrate;

exec "$@"
