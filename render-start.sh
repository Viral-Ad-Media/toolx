#!/bin/sh
set -eu
# Use the unpooled connection for release operations, not normal application traffic.
DATABASE_URL="${DATABASE_URL_UNPOOLED:?Set DATABASE_URL_UNPOOLED for migrations}" python manage.py migrate --noinput
DATABASE_URL="$DATABASE_URL_UNPOOLED" python manage.py bootstrap_admin
exec gunicorn toolx.wsgi:application --bind "0.0.0.0:${PORT:-10000}" --workers 2 --threads 2 --timeout 120 --access-logfile - --error-logfile -
