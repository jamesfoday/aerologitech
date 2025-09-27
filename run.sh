#!/usr/bin/env bash
set -e

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.prod}"

python --version
echo "▶ Running migrations…"
python manage.py migrate --noinput

echo "▶ Collecting static (Cloudinary disabled)…"
USE_CLOUDINARY_MEDIA=false python manage.py collectstatic --noinput

echo "▶ Starting gunicorn…"
gunicorn config.wsgi:application \
  --bind 0.0.0.0:${PORT:-10000} \
  --workers ${WEB_CONCURRENCY:-2} \
  --timeout ${GUNICORN_TIMEOUT:-60}
