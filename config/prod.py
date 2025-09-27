# config/prod.py
from __future__ import annotations

import os
import dj_database_url

from .base import *  # noqa

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", SECRET_KEY)  # type: ignore[name-defined]

# ----- Hosts / CSRF
_raw_hosts = os.getenv("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for chunk in _raw_hosts.split(",") for h in chunk.split() if h.strip()] or ["*"]

_raw_csrf = os.getenv("CSRF_TRUSTED_ORIGINS", "")
if _raw_csrf.strip():
    CSRF_TRUSTED_ORIGINS = [o.strip() for chunk in _raw_csrf.split(",") for o in chunk.split() if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS if "." in h and not h.startswith(".")]
    if "https://*.onrender.com" not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append("https://*.onrender.com")

# ----- DB
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/db.sqlite3"),  # type: ignore[name-defined]
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,
    )
}

# ----- Static/Media
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

# 🔑 NEW: gate Cloudinary by env var so we can turn it OFF during collectstatic.
USE_CLOUDINARY = (
    os.getenv("USE_CLOUDINARY_MEDIA", "true").lower() == "true"
    and bool(os.getenv("CLOUDINARY_URL"))
)

# Ensure cloudinary apps are correct (we only need cloudinary_storage, not 'cloudinary')
if USE_CLOUDINARY:
    if "cloudinary_storage" in INSTALLED_APPS:
        INSTALLED_APPS.remove("cloudinary_storage")
    if "django.contrib.staticfiles" in INSTALLED_APPS:
        idx = INSTALLED_APPS.index("django.contrib.staticfiles")
        INSTALLED_APPS.insert(idx, "cloudinary_storage")
    else:
        INSTALLED_APPS += ["cloudinary_storage"]

# Never keep the 'cloudinary' Django app (it adds static JS we don't need)
if "cloudinary" in INSTALLED_APPS:
    INSTALLED_APPS.remove("cloudinary")

if USE_CLOUDINARY:
    STORAGES = {
        "default": {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    CLOUDINARY_STORAGE = {"SECURE": True}
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }

# Legacy aliases for libs that still read old names
STATICFILES_STORAGE = STORAGES["staticfiles"]["BACKEND"]
if USE_CLOUDINARY:
    DEFAULT_FILE_STORAGE = STORAGES["default"]["BACKEND"]

WHITENOISE_SKIP_COMPRESS_EXTENSIONS = [".map"]
WHITENOISE_MANIFEST_STRICT = os.getenv("WHITENOISE_MANIFEST_STRICT", "true").lower() == "true"
MEDIA_URL = "/media/"

# ----- Security
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "true").lower() == "true"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ----- Email (optional)
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", EMAIL_BACKEND)  # type: ignore[name-defined]
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587")) if EMAIL_HOST else 587
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"

# ----- Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}
