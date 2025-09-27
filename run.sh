#!/usr/bin/env bash
set -Eeuo pipefail
set -x  # debug: echo commands so we see them in Render logs

# Default to prod settings
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.prod}"

python --version
echo "▶ Running migrations..."
python manage.py migrate --noinput

echo "▶ Collecting static..."
python manage.py collectstatic --noinput

echo "▶ Starting gunicorn..."
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-10000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-60}"
