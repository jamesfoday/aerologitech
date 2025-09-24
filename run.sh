#!/usr/bin/env bash
set -e

# Optional: show where we are
echo "Starting Django with settings: ${DJANGO_SETTINGS_MODULE:-config.settings}"

# Collect static files for Whitenoise / CDN
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate --noinput

# Start Gunicorn (the $PORT env var is provided by the host, e.g. Railway/Render/Fly)
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:"${PORT:-8000}" \
  --workers 3 \
  --timeout 60
