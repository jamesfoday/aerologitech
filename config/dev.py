from __future__ import annotations
import os
from pathlib import Path
import dj_database_url

from .base import *  # noqa

# -------------------- FLAGS -------------------- #
DEBUG = True  # dev on by default; override with DEBUG=false 

# -------------------- HOSTS / CSRF -------------------- #
ALLOWED_HOSTS = [
    "localhost", "127.0.0.1", "::1",
]
#  env too 
ALLOWED_HOSTS += [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]

# Local dev usually runs over HTTP, so no CSRF trusted origins required.
# ( https://... for test via a tunneled https URL.)

# config/dev.py




# -------------------- DATABASE -------------------- #
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/db.sqlite3"),
        conn_max_age=0,            # no persistent connections for dev
        conn_health_checks=True,
    )
}

# -------------------- STATIC (WhiteNoise ok in dev too) -------------------- #

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

# Use the modern STORAGES setting (Django 5+). This replaces STATICFILES_STORAGE.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Create STATIC_ROOT if it doesn't exist (prevents the dev warning you saw)
Path(STATIC_ROOT).mkdir(parents=True, exist_ok=True)

# -------------------- SECURITY (DEV-FRIENDLY) -------------------- #
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = False           # IMPORTANT: No HTTPS redirect in dev
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# -------------------- EMAIL (console) -------------------- #
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")

# -------------------- OPTIONAL CLOUDINARY  -------------------- #
if os.getenv("CLOUDINARY_URL"):
    INSTALLED_APPS += ["cloudinary", "cloudinary_storage"]
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
